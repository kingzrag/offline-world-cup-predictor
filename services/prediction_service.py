from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ml.predictor import FootballPredictor
from models import Match, Prediction, Competition
from services.model_service import model_service
from services.prediction_tracking_service import prediction_tracking_service
from utils.logger import logger


class PredictionService:
    """
    Orchestration service for calculating and storing match win probabilities.
    Routes ML inference dynamically across all supported competitions.
    """

    def __init__(self):
        self.predictor = FootballPredictor()

    def generate_predictions_for_fixtures(self, db: Session, competition_id: Optional[int] = None) -> List[Prediction]:
        """
        Retrieves upcoming SCHEDULED/TIMED matches and calculates game prediction probabilities.
        Upserts records into the Predictions table.
        """
        logger.info("Initializing bulk match predictions pipeline...")

        query = db.query(Match).filter(Match.status.in_(["SCHEDULED", "TIMED"]))
        if competition_id:
            query = query.filter(Match.competition_id == competition_id)

        scheduled_matches = query.all()
        logger.info(f"Retrieved {len(scheduled_matches)} upcoming fixtures for prediction generation.")

        predictions_created = []

        for match in scheduled_matches:
            try:
                comp_code = match.competition.code if (match.competition and match.competition.code) else "PL"
                prediction_res = self.predictor.predict_outcome(
                    db=db,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    match_date=match.utc_date,
                    competition_code=comp_code
                )

                logger.info(
                    f"Generated prediction for [{comp_code}] {match.home_team.name} vs {match.away_team.name}: "
                    f"{prediction_res['predicted_outcome']}"
                )

                pred_winner_id = None
                predicted_outcome = prediction_res["predicted_outcome"]
                if predicted_outcome == "HOME_WIN":
                    pred_winner_id = match.home_team_id
                elif predicted_outcome == "AWAY_WIN":
                    pred_winner_id = match.away_team_id

                existing_pred = db.query(Prediction).filter_by(match_id=match.id).first()
                if not existing_pred:
                    existing_pred = Prediction(
                        match_id=match.id,
                        predicted_winner_id=pred_winner_id,
                        predicted_outcome=predicted_outcome,
                        home_probability=prediction_res["home_probability"],
                        away_probability=prediction_res["away_probability"],
                        draw_probability=prediction_res["draw_probability"],
                        model_version=prediction_res["model_version"]
                    )
                    db.add(existing_pred)
                else:
                    existing_pred.predicted_winner_id = pred_winner_id
                    existing_pred.predicted_outcome = predicted_outcome
                    existing_pred.home_probability = prediction_res["home_probability"]
                    existing_pred.away_probability = prediction_res["away_probability"]
                    existing_pred.draw_probability = prediction_res["draw_probability"]
                    existing_pred.model_version = prediction_res["model_version"]

                predictions_created.append(existing_pred)

            except Exception as e:
                logger.error(f"Failed to generate prediction for Match ID {match.id} (API ID {match.api_id}): {str(e)}")
                continue

        db.commit()
        logger.info(f"Successfully calculated and committed {len(predictions_created)} match predictions.")
        return predictions_created

    def generate_enrichment_for_fixtures(
        self,
        db: Session,
        competition_id: Optional[int] = None,
        *,
        statuses: Optional[List[str]] = None,
    ) -> int:
        """
        Pre-compute expected goals for fixtures and persist on Prediction rows.
        Runs ML inference offline.
        """
        if not model_service.is_ready:
            model_service.load_models()

        status_filter = statuses or ["SCHEDULED", "TIMED", "IN_PLAY", "PAUSED"]
        query = db.query(Match).filter(Match.status.in_(status_filter))
        if competition_id:
            query = query.filter(Match.competition_id == competition_id)

        matches = query.all()
        logger.info(f"Enrichment pipeline: {len(matches)} fixtures to process.")

        comp_code_map: Dict[int, str] = {
            c.id: c.code
            for c in db.query(Competition).all()
            if c.code
        }

        updated = 0
        for match in matches:
            try:
                comp_code = comp_code_map.get(match.competition_id, "PL") if match.competition_id else "PL"

                goals = model_service.predict_goals(
                    db=db,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    match_date=match.utc_date,
                    competition_code=comp_code,
                )

                existing_pred = db.query(Prediction).filter_by(match_id=match.id).first()
                if not existing_pred:
                    existing_pred = Prediction(
                        match_id=match.id,
                        predicted_outcome="DRAW",
                        home_probability=0.33,
                        away_probability=0.33,
                        draw_probability=0.34,
                        model_version="pending",
                    )
                    db.add(existing_pred)

                existing_pred.expected_home_goals = goals["expected_home_goals"]
                existing_pred.expected_away_goals = goals["expected_away_goals"]
                
                self._store_betting_market_predictions(
                    db, match, goals, goals.get("model_version", "unknown")
                )
                
                updated += 1
            except Exception as e:
                logger.error(
                    f"Failed to generate enrichment for Match ID {match.id} "
                    f"(API ID {match.api_id}): {e}"
                )
                continue

        db.commit()
        logger.info(f"Enrichment pipeline complete — {updated} fixtures updated.")
        return updated

    def get_predictions_history(self, db: Session, limit: int = 100) -> List[Prediction]:
        """
        Serving pre-calculated prediction history entries.
        """
        return db.query(Prediction).order_by(Prediction.created_at.desc()).limit(limit).all()

    def _store_betting_market_predictions(
        self, db: Session, match: Match, goals: Dict[str, Any], model_version: str
    ) -> None:
        """
        Store betting market predictions for tracking.
        """
        try:
            ah_label = goals.get("asian_handicap", {}).get("label", "Level (0)")
            prediction_tracking_service.store_betting_market_prediction(
                db=db,
                match_id=match.id,
                market_type="asian_handicap",
                predicted_value=ah_label,
                predicted_probability=None,
                model_version=model_version,
                source="poisson_fallback",
                prediction_data=goals.get("asian_handicap"),
            )

            ou_2_5 = goals.get("over_under", {}).get("2.5", {})
            over_prob = ou_2_5.get("over", 0.5)
            prediction_tracking_service.store_betting_market_prediction(
                db=db,
                match_id=match.id,
                market_type="asian_total",
                predicted_value="Over" if over_prob > 0.5 else "Under",
                predicted_probability=over_prob,
                model_version=model_version,
                source="poisson_fallback",
                prediction_data=goals.get("over_under"),
            )

            btts = goals.get("btts", {})
            btts_yes_prob = btts.get("yes", 0.5)
            prediction_tracking_service.store_betting_market_prediction(
                db=db,
                match_id=match.id,
                market_type="btts",
                predicted_value="Yes" if btts_yes_prob > 0.5 else "No",
                predicted_probability=btts_yes_prob,
                model_version=model_version,
                source="poisson_fallback",
                prediction_data=btts,
            )

            cs = goals.get("clean_sheet", {})
            home_cs_prob = cs.get("home_clean_sheet", 0.5)
            prediction_tracking_service.store_betting_market_prediction(
                db=db,
                match_id=match.id,
                market_type="clean_sheet",
                predicted_value="Yes" if home_cs_prob > 0.5 else "No",
                predicted_probability=home_cs_prob,
                model_version=model_version,
                source="poisson_fallback",
                prediction_data=cs,
            )

            most_likely = goals.get("most_likely_score", "1-1")
            top_5 = goals.get("top_5_scorelines", [])
            top_prob = top_5[0].get("probability", 0.0) if top_5 else 0.0
            prediction_tracking_service.store_betting_market_prediction(
                db=db,
                match_id=match.id,
                market_type="correct_score",
                predicted_value=most_likely,
                predicted_probability=top_prob,
                model_version=model_version,
                source="poisson_fallback",
                prediction_data={"most_likely_score": most_likely, "top_5_scorelines": top_5},
            )

            existing_pred = db.query(Prediction).filter_by(match_id=match.id).first()
            if existing_pred:
                confidence = max(
                    existing_pred.home_probability,
                    existing_pred.draw_probability,
                    existing_pred.away_probability,
                )
                prediction_tracking_service.store_betting_market_prediction(
                    db=db,
                    match_id=match.id,
                    market_type="match_winner",
                    predicted_value=existing_pred.predicted_outcome,
                    predicted_probability=confidence,
                    model_version=existing_pred.model_version,
                    source="ml_model",
                    prediction_data={
                        "confidence": confidence,
                        "home_prob": existing_pred.home_probability,
                        "draw_prob": existing_pred.draw_probability,
                        "away_prob": existing_pred.away_probability,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to store betting market predictions for match {match.id}: {e}", exc_info=True)

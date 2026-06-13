from sqlalchemy.orm import Session
from typing import List, Optional

from ml.predictor import FootballPredictor
from models import Match, Prediction
from utils.logger import logger

class PredictionService:
    """
    Orchestration service for calculating and storing match win probabilities.
    Routes all ML inference through FootballPredictor (xgboost_model.json).
    """

    def __init__(self):
        self.predictor = FootballPredictor()

    def generate_predictions_for_fixtures(self, db: Session, competition_id: Optional[int] = None) -> List[Prediction]:
        """
        Retrieves upcoming SCHEDULED/TIMED matches and calculates game prediction probabilities.
        Upserts records into the Predictions table.
        """
        logger.info("Initializing bulk match predictions pipeline...")

        # 1. Fetch scheduled/timed matches
        query = db.query(Match).filter(Match.status.in_(["SCHEDULED", "TIMED"]))
        if competition_id:
            query = query.filter(Match.competition_id == competition_id)

        scheduled_matches = query.all()
        logger.info(f"Retrieved {len(scheduled_matches)} upcoming fixtures for prediction generation.")

        predictions_created = []

        for match in scheduled_matches:
            try:
                # Run prediction via FootballPredictor
                prediction_res = self.predictor.predict_outcome(
                    db=db,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    match_date=match.utc_date,
                    competition_code="WC"
                )

                logger.info(
                    f"Generated prediction for {match.home_team.name} vs {match.away_team.name}: "
                    f"{prediction_res['predicted_outcome']}"
                )

                # Resolve predicted winner
                pred_winner_id = None
                predicted_outcome = prediction_res["predicted_outcome"]
                if predicted_outcome == "HOME_WIN":
                    pred_winner_id = match.home_team_id
                elif predicted_outcome == "AWAY_WIN":
                    pred_winner_id = match.away_team_id

                # Upsert Prediction record
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

        # Commit all calculations atomically
        db.commit()
        logger.info(f"Successfully calculated and committed {len(predictions_created)} match predictions.")
        return predictions_created

    def get_predictions_history(self, db: Session, limit: int = 50) -> List[Prediction]:
        """
        Serving pre-calculated prediction history entries.
        """
        return db.query(Prediction).order_by(Prediction.created_at.desc()).limit(limit).all()


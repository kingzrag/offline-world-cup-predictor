"""
services/model_service.py
=========================
Singleton service that loads both ML models ONCE at startup.

    - world_cup_predictor.pkl  → 1X2 outcome probabilities
    - goal_predictor.pkl       → expected home/away goals + all betting markets

Never reloads per-request; safe for async FastAPI lifecycle.
"""

import os
import pickle
import logging
import math
import numpy as np
import xgboost as xgb
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

from services.poisson_engine import evaluate_poisson_engine, POISSON_ENGINE_VERSION

# ── Resolved paths ────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_MODELS_DIR = os.path.join(_ROOT, "models")

WC_MODEL_PATH   = os.path.join(_MODELS_DIR, "world_cup_predictor.pkl")
GOAL_MODEL_PATH = os.path.join(_MODELS_DIR, "goal_predictor.pkl")

# Betting market model paths (optional)
BETTING_MODEL_PATHS = {
    "asian_handicap": os.path.join(_MODELS_DIR, "asian_handicap_predictor.pkl"),
    "asian_total": os.path.join(_MODELS_DIR, "asian_total_predictor.pkl"),
    "btts": os.path.join(_MODELS_DIR, "btts_predictor.pkl"),
    "clean_sheet": os.path.join(_MODELS_DIR, "clean_sheet_predictor.pkl"),
    "correct_score": os.path.join(_MODELS_DIR, "correct_score_predictor.pkl"),
}


class ModelService:
    """
    Production singleton that owns both trained model artifacts.

    Usage (from any route):
        from services.model_service import model_service
        result = model_service.predict(home_team_name, away_team_name, db)
    """

    _instance: Optional["ModelService"] = None

    # ── Singleton constructor ─────────────────────────────────────────────────
    def __new__(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    # ── Lazy initialiser (called once from startup event) ─────────────────────
    def load_models(self) -> None:
        if self._initialized:
            return

        logger.info("ModelService: loading world_cup_predictor.pkl …")
        if not os.path.exists(WC_MODEL_PATH):
            raise FileNotFoundError(f"world_cup_predictor.pkl not found at {WC_MODEL_PATH}")
        with open(WC_MODEL_PATH, "rb") as f:
            self._wc_bundle: Dict[str, Any] = pickle.load(f)
        logger.info("ModelService: world_cup_predictor.pkl loaded ✓")

        logger.info("ModelService: loading goal_predictor.pkl …")
        if not os.path.exists(GOAL_MODEL_PATH):
            raise FileNotFoundError(f"goal_predictor.pkl not found at {GOAL_MODEL_PATH}")
        with open(GOAL_MODEL_PATH, "rb") as f:
            self._goal_bundle: Dict[str, Any] = pickle.load(f)
        logger.info("ModelService: goal_predictor.pkl loaded ✓")

        # Optionally load betting market models (non-critical)
        self._betting_models: Dict[str, Dict[str, Any]] = {}
        for market_name, model_path in BETTING_MODEL_PATHS.items():
            if os.path.exists(model_path):
                try:
                    logger.info(f"ModelService: loading {market_name}_predictor.pkl …")
                    with open(model_path, "rb") as f:
                        self._betting_models[market_name] = pickle.load(f)
                    logger.info(f"ModelService: {market_name}_predictor.pkl loaded ✓")
                except Exception as e:
                    logger.warning(f"ModelService: failed to load {market_name}_predictor.pkl: {e}")
            else:
                logger.info(f"ModelService: {market_name}_predictor.pkl not found (will use Poisson fallback)")

        self._initialized = True
        logger.info("ModelService: both models ready.")

    # ── Confidence calculation methods ────────────────────────────────────────
    @staticmethod
    def normalize_1x2_probs(home_p: float, draw_p: float, away_p: float) -> tuple[float, float, float]:
        """
        Normalize 1X2 probabilities to sum exactly to 1.0, rounding to 4 decimal places.
        
        This ensures frontend receives consistent probabilities that always sum to 1.0,
        preventing floating-point arithmetic errors that could cause 0.9999 or 1.0001 sums.
        
        Strategy:
        1. Round each probability to 4 decimal places for readability
        2. If sum is exactly 1.0, return as-is
        3. Otherwise, adjust the largest probability to absorb the rounding error
           (this minimizes visual impact on the most likely outcome)
        
        Args:
            home_p: Home win probability (0-1)
            draw_p: Draw probability (0-1)
            away_p: Away win probability (0-1)
        
        Returns:
            (normalized_home, normalized_draw, normalized_away) - probabilities summing to 1.0
        """
        # Step 1: Round each to 4 decimal places for consistent display
        h = round(home_p, 4)
        d = round(draw_p, 4)
        a = round(away_p, 4)
        
        # Step 2: Check if rounding already produced perfect sum
        total = h + d + a
        if total == 1.0:
            return h, d, a
        
        # Step 3: Adjust the largest probability to absorb rounding error
        # This minimizes visual impact on the most likely outcome
        diff = 1.0 - total
        if h >= d and h >= a:
            return h + diff, d, a
        elif d >= h and d >= a:
            return h, d + diff, a
        else:
            return h, d, a + diff

    # NOTE: calculate_probability_entropy removed - unused method

    @staticmethod
    def calculate_confidence(home_p: float, draw_p: float, away_p: float) -> tuple[float, str]:
        """
        Calculate confidence score and confidence level from 1X2 probabilities.
        
        Confidence is measured as the margin between the top two probabilities.
        A larger margin indicates higher confidence in the predicted outcome.
        
        Strategy:
        1. Sort probabilities to find top two
        2. Calculate margin (top1 - top2) as confidence metric
        3. Classify confidence level based on margin thresholds
        
        Args:
            home_p: Home win probability (0-1)
            draw_p: Draw probability (0-1)
            away_p: Away win probability (0-1)
        
        Returns:
            (confidence_score, confidence_level)
            confidence_score: Margin between top two probabilities [0,1], rounded to 4 decimals
            confidence_level: "Low", "Medium", "High", or "Very High"
        """
        probs = [home_p, draw_p, away_p]
        
        # Sort probabilities to find top two
        sorted_probs = sorted(probs, reverse=True)
        top1_prob = sorted_probs[0]
        top2_prob = sorted_probs[1]
        
        # Calculate margin (top1 - top2) as our primary confidence metric
        margin = top1_prob - top2_prob
        
        # Margin is already normalized to [0,1] since max possible margin is ~1
        confidence_score = margin
        
        # Determine confidence level based on margin thresholds
        # These thresholds are empirically chosen for sensible categorization
        if confidence_score >= 0.5:
            confidence_level = "Very High"
        elif confidence_score >= 0.2:
            confidence_level = "High"
        elif confidence_score >= 0.05:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"
        
        return round(confidence_score, 4), confidence_level

    # ── Health status ─────────────────────────────────────────────────────────
    @property
    def is_ready(self) -> bool:
        return self._initialized

    @property
    def model_versions(self) -> Dict[str, str]:
        if not self._initialized:
            return {"wc_model": "not_loaded", "goal_model": "not_loaded"}
        versions = {
            "wc_model":   self._wc_bundle.get("version", "unknown"),
            "goal_model": self._goal_bundle.get("version", "unknown"),
        }
        # Add betting market model versions if loaded
        for market_name, bundle in self._betting_models.items():
            versions[f"{market_name}_model"] = bundle.get("version", "unknown")
        return versions

    # ── Internal: extract features ────────────────────────────────────────────
    def _get_features(self, db, home_team_id: int, away_team_id: int,
                      match_date, competition_code: str = "WC",
                      match_stage: Optional[str] = None,
                      match=None) -> Dict[str, float]:
        from ml.features import extract_ml_features
        return extract_ml_features(
            db, home_team_id, away_team_id, match_date,
            competition_code=competition_code,
            match_stage=match_stage,
            match=match,
        )

    # ── 1X2 Prediction ────────────────────────────────────────────────────────
    def predict_1x2(self, db, home_team_id: int, away_team_id: int,
                    match_date=None, competition_code: str = "WC", match=None) -> Dict[str, Any]:
        """
        Returns Home Win / Draw / Away Win probabilities using world_cup_predictor.pkl.
        
        Process:
        1. Extract ML features from database
        2. Run XGBoost classifier to get raw probabilities
        3. Normalize probabilities to ensure they sum exactly to 1.0
        4. Determine predicted outcome (highest probability)
        5. Return structured response with probabilities and metadata
        
        Args:
            db: Database session
            home_team_id: ID of home team
            away_team_id: ID of away team
            match_date: Match date (defaults to now)
            competition_code: Competition code (defaults to WC)
            match: Optional match record for feature extraction
        
        Returns:
            Dictionary with home_win_probability, draw_probability, away_win_probability,
            predicted_outcome, confidence, and model_version
        """
        if not self._initialized:
            raise RuntimeError("ModelService not initialised – call load_models() first.")

        match_date = match_date or datetime.now(timezone.utc)

        # Resolve team names for logging
        from models import Team as _Team
        _home = db.query(_Team).filter_by(id=home_team_id).first()
        _away = db.query(_Team).filter_by(id=away_team_id).first()
        _home_name = _home.name if _home else str(home_team_id)
        _away_name = _away.name if _away else str(away_team_id)
        logger.info(f"[predict_1x2] {_home_name} vs {_away_name} [{competition_code}]")

        # Extract ML features from database
        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code, match=match)

        # Load model and feature names from bundle
        wc_features: list = self._wc_bundle.get("features", [])
        model: xgb.XGBClassifier = self._wc_bundle["model"]

        # Build feature vector in the order expected by the model
        feature_vec = [features.get(f, 0.0) for f in wc_features]

        # Log full feature dict and final vector for debugging
        logger.info(f"[predict_1x2] Extracted features for {_home_name} vs {_away_name}:")
        for k, v in features.items():
            logger.info(f"  {k:<40} = {v}")
        logger.info(f"[predict_1x2] Feature vector ({len(feature_vec)} values): {[round(v, 4) for v in feature_vec]}")

        # Run model prediction
        df_input    = __import__("pandas").DataFrame([feature_vec], columns=wc_features)
        probs = model.predict_proba(df_input)[0]
        
        # Training label mapping: 0 = Away Win, 1 = Draw, 2 = Home Win
        prob_away, prob_draw, prob_home = float(probs[0]), float(probs[1]), float(probs[2])
        logger.info(
            f"[predict_1x2] Raw model probs for {_home_name} vs {_away_name}: "
            f"home={prob_home:.4f}  draw={prob_draw:.4f}  away={prob_away:.4f}"
        )
        
        # Normalize probabilities to sum exactly to 1.0 for consistency
        prob_home, prob_draw, prob_away = ModelService.normalize_1x2_probs(
            prob_home, prob_draw, prob_away
        )

        # Determine predicted outcome (highest probability)
        max_p = max(prob_home, prob_away, prob_draw)
        if max_p == prob_home:
            outcome = "HOME_WIN"
            confidence = prob_home
        elif max_p == prob_away:
            outcome = "AWAY_WIN"
            confidence = prob_away
        else:
            outcome = "DRAW"
            confidence = prob_draw

        return {
            "home_win_probability": prob_home,
            "draw_probability":     prob_draw,
            "away_win_probability": prob_away,
            "predicted_outcome":    outcome,
            "confidence":           round(confidence, 4),
            "model_version":        self._wc_bundle.get("version", "v1.0"),
        }

    # ── Goal Prediction ───────────────────────────────────────────────────────
    def predict_goals(self, db, home_team_id: int, away_team_id: int,
                      match_date=None, competition_code: str = "WC", match=None) -> Dict[str, Any]:
        """
        Returns expected goals + full betting market suite via Poisson engine.
        
        Process:
        1. Extract ML features from database
        2. Run XGBoost regressors to predict expected home/away goals
        3. Clip negative predictions to 0 (goals cannot be negative)
        4. Run Poisson engine to generate all betting markets from xG
        5. Return structured response with goals, markets, and metadata
        
        Args:
            db: Database session
            home_team_id: ID of home team
            away_team_id: ID of away team
            match_date: Match date (defaults to now)
            competition_code: Competition code (defaults to WC)
            match: Optional match record for feature extraction
        
        Returns:
            Dictionary with expected_home_goals, expected_away_goals, total_expected_goals,
            over_under markets, btts, most_likely_score, top_5_scorelines, asian_handicap,
            team_goals, clean_sheet, probability_matrix, outcome_probabilities, and model_version
        """
        if not self._initialized:
            raise RuntimeError("ModelService not initialised – call load_models() first.")

        match_date = match_date or datetime.now(timezone.utc)

        # Resolve team names for logging
        from models import Team as _Team
        _home = db.query(_Team).filter_by(id=home_team_id).first()
        _away = db.query(_Team).filter_by(id=away_team_id).first()
        _home_name = _home.name if _home else str(home_team_id)
        _away_name = _away.name if _away else str(away_team_id)
        logger.info(f"[predict_goals] {_home_name} vs {_away_name} [{competition_code}]")

        # Extract ML features from database
        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code, match=match)

        # Load goal prediction models and feature names
        goal_features: list = self._goal_bundle.get("features", [])
        home_model: xgb.XGBRegressor = self._goal_bundle["home_model"]
        away_model: xgb.XGBRegressor = self._goal_bundle["away_model"]

        # Build feature vector in the order expected by the models
        feature_vals = [features.get(f, 0.0) for f in goal_features]

        # Log full feature dict and final vector for debugging
        logger.info(f"[predict_goals] Extracted features for {_home_name} vs {_away_name}:")
        for k, v in features.items():
            logger.info(f"  {k:<40} = {v}")
        logger.info(f"[predict_goals] Feature vector ({len(feature_vals)} values) for goal models: {[round(v, 4) if isinstance(v, (int, float)) else v for v in feature_vals]}")

        # Validate feature vector (check for NaN or zero-only vectors)
        import math
        has_nan = any(isinstance(v, float) and math.isnan(v) for v in feature_vals)
        all_zeros = all(v == 0.0 for v in feature_vals)
        if has_nan:
            logger.warning(f"[predict_goals] NaN detected in feature vector for {_home_name} vs {_away_name}!")
        if all_zeros:
            logger.warning(f"[predict_goals] Zero-only feature vector detected for {_home_name} vs {_away_name}!")

        # Run goal prediction models
        feature_vec = np.array([feature_vals])
        raw_home = float(home_model.predict(feature_vec)[0])
        raw_away = float(away_model.predict(feature_vec)[0])
        logger.info(
            f"[predict_goals] RAW OUTPUTS: "
            f"{_home_name}={raw_home:.4f}, "
            f"{_away_name}={raw_away:.4f}"
        )

        # Clip negative predictions to 0 (goals cannot be negative)
        expected_home = max(0.0, raw_home)
        expected_away = max(0.0, raw_away)
        clipped_home = raw_home != expected_home
        clipped_away = raw_away != expected_away

        logger.info(
            f"[predict_goals] CLIPPED OUTPUTS: "
            f"{_home_name}={expected_home:.4f}, "
            f"{_away_name}={expected_away:.4f}"
        )
        if clipped_home or clipped_away:
            logger.info(
                f"[predict_goals] Clipping occurred: "
                f"home={'yes' if clipped_home else 'no'}, "
                f"away={'yes' if clipped_away else 'no'}"
            )
        if raw_home < 0 or raw_away < 0:
            logger.warning(
                f"[predict_goals] Negative prediction detected before clipping: "
                f"home={raw_home:.4f}, away={raw_away:.4f}"
            )

        total_goals   = expected_home + expected_away

        logger.info(f"[predict_goals] Expected Goals predicted: {_home_name}={expected_home:.4f}, {_away_name}={expected_away:.4f}, Total={total_goals:.4f}")

        # Generate all betting markets using Poisson engine
        from services.poisson_engine import evaluate_poisson_engine
        poisson = evaluate_poisson_engine(expected_home, expected_away)

        ou   = poisson["over_under"]
        btts = poisson["btts"]

        # Calculate Asian handicap label based on xG difference
        diff = expected_home - expected_away
        if diff > 1.5:
            asian_handicap_label = "Home -1.5"
        elif diff > 0.5:
            asian_handicap_label = "Home -0.5"
        elif diff > -0.5:
            asian_handicap_label = "Level (0)"
        elif diff > -1.5:
            asian_handicap_label = "Away -0.5"
        else:
            asian_handicap_label = "Away -1.5"

        return {
            "expected_home_goals":  round(expected_home, 4),
            "expected_away_goals":  round(expected_away, 4),
            "total_expected_goals": round(total_goals, 4),
            # Over / Under markets (0.5 – 4.5)
            "over_under": poisson["over_under"],
            # BTTS (Both Teams To Score)
            "btts": {
                "yes": btts["btts_yes"],
                "no":  btts["btts_no"],
            },
            # Correct score predictions
            "most_likely_score":  poisson["most_likely_score"],
            "top_5_scorelines":   poisson["top_5_scorelines"],
            # Asian handicap markets
            "asian_handicap": {
                "label":        asian_handicap_label,
                "lines":        poisson["asian_handicap"]["suggested_lines"],
                "favored_team": poisson["asian_handicap"]["favored_team_prefix"],
            },
            # Team goals markets (over 0.5, 1.5, 2.5)
            "team_goals":          poisson["team_goals"],
            # Clean sheet probabilities (P(0) = e^(-lambda))
            "clean_sheet":         poisson["clean_sheet"],
            # Full probability matrix for all scorelines
            "probability_matrix":  poisson["probability_matrix"],
            # Outcome probabilities (from Poisson matrix for consistency with 1X2)
            "outcome_probabilities": poisson["outcome_probabilities"],
            "model_version":       self._goal_bundle.get("version", "v1.0"),
        }
        logger.info(f"[PREDICT_GOALS] Asian handicap from Poisson: label={asian_handicap_label}, lines={poisson['asian_handicap']['suggested_lines']}, favored={poisson['asian_handicap']['favored_team_prefix']}")

    # ── Combined full prediction ───────────────────────────────────────────────
    def predict(self, db, home_team_name: str, away_team_name: str,
                competition_code: str = "WC") -> Dict[str, Any]:
        """
        Full prediction combining 1X2 + goals + all markets.
        Resolves team names to IDs internally.

        Raises ValueError if either team is not found in the database.
        """
        from models import Team, Match, Competition

        # Resolve team name aliases for United States
        aliases = {
            "USA": "United States",
            "US": "United States",
            "UNITED STATES OF AMERICA": "United States"
        }
        h_clean = home_team_name.strip().upper()
        if h_clean in aliases:
            home_team_name = aliases[h_clean]

        a_clean = away_team_name.strip().upper()
        if a_clean in aliases:
            away_team_name = aliases[a_clean]

        home = db.query(Team).filter(Team.name.ilike(home_team_name)).first()
        if not home:
            # fuzzy fallback
            home = db.query(Team).filter(Team.name.ilike(f"%{home_team_name}%")).first()
        if not home:
            raise ValueError(f"Team not found: '{home_team_name}'")

        away = db.query(Team).filter(Team.name.ilike(away_team_name)).first()
        if not away:
            away = db.query(Team).filter(Team.name.ilike(f"%{away_team_name}%")).first()
        if not away:
            raise ValueError(f"Team not found: '{away_team_name}'")

        target_comp = db.query(Competition).filter_by(code=competition_code).first()
        match_record = None
        if target_comp:
            match_record = db.query(Match).filter(
                Match.home_team_id == home.id,
                Match.away_team_id == away.id,
                Match.competition_id == target_comp.id
            ).order_by(Match.utc_date.desc()).first()

        now = datetime.now(timezone.utc)

        # ── Fixture identity guard ─────────────────────────────────────────────
        # The query above finds the *most recent* historical match for this team
        # pair + competition.  Without a guard, a match played years ago (e.g.
        # France vs Sweden Friendly 2014) would suppress the ML prediction for
        # any future fixture between the same teams.
        #
        # Resolution priority (most precise → fallback):
        #   1. Upcoming / live: status is TIMED, SCHEDULED, IN_PLAY or PAUSED
        #      → keep match_record as model context but DO NOT treat as a result.
        #   2. Recently completed: status == FINISHED AND kickoff within 7 days
        #      → treat as the actual result and apply override.
        #   3. Old completed: status == FINISHED AND kickoff older than 7 days
        #      → null out match_record; run full ML + Poisson prediction.
        if match_record and match_record.status == "FINISHED":
            match_date_utc = match_record.utc_date
            if match_date_utc.tzinfo is None:
                match_date_utc = match_date_utc.replace(tzinfo=timezone.utc)
            age = now - match_date_utc
            if age.days > 7:
                # Too old to be the fixture being predicted — discard it so the
                # ML pipeline runs on fresh Poisson predictions.
                logger.info(
                    f"[predict] Discarding stale match_record id={match_record.id} "
                    f"({home.name} vs {away.name}, date={match_record.utc_date.date()}, "
                    f"age={age.days}d) — running ML prediction instead."
                )
                match_record = None

        if match_record and match_record.status == "FINISHED":
            # Override with real results
            home_score = match_record.home_score if match_record.home_score is not None else 0
            away_score = match_record.away_score if match_record.away_score is not None else 0
            winner = match_record.winner or "DRAW"
            
            if winner == "HOME_TEAM":
                predicted_result = "HOME_WIN"
                prob_home, prob_draw, prob_away = 1.0, 0.0, 0.0
            elif winner == "AWAY_TEAM":
                predicted_result = "AWAY_WIN"
                prob_home, prob_draw, prob_away = 0.0, 0.0, 1.0
            else:
                predicted_result = "DRAW"
                prob_home, prob_draw, prob_away = 0.0, 1.0, 0.0

            total_goals = home_score + away_score
            
            # Correct Score top_5_scorelines
            most_likely_score = f"{home_score}-{away_score}"
            top_5_scorelines = [{"score": most_likely_score, "probability": 1.0}]
            dummy_scores = ["0-0", "1-1", "1-0", "0-1", "2-1", "1-2"]
            for ds in dummy_scores:
                if ds != most_likely_score and len(top_5_scorelines) < 5:
                    top_5_scorelines.append({"score": ds, "probability": 0.0})

            # Over / Under
            over_under = {
                "1.5": {"over": 1.0 if total_goals > 1.5 else 0.0, "under": 0.0 if total_goals > 1.5 else 1.0},
                "2.5": {"over": 1.0 if total_goals > 2.5 else 0.0, "under": 0.0 if total_goals > 2.5 else 1.0},
                "3.5": {"over": 1.0 if total_goals > 3.5 else 0.0, "under": 0.0 if total_goals > 3.5 else 1.0},
            }

            # BTTS
            btts_yes = 1.0 if home_score > 0 and away_score > 0 else 0.0
            btts_no = 1.0 - btts_yes
            btts = {"yes": btts_yes, "no": btts_no}

            # Asian handicap calculation based on actual score difference
            diff = home_score - away_score
            is_home_fav = diff >= 0
            prefix = "Home" if is_home_fav else "Away"
            goal_diff = abs(diff)
            lines = [-0.25, -0.5, -0.75, -1.0]
            suggested_lines = {}
            for line in lines:
                val = 0.0
                if line == -0.25:
                    val = 1.0 if goal_diff >= 1 else (0.5 if goal_diff == 0 else 0.0)
                elif line == -0.5:
                    val = 1.0 if goal_diff >= 1 else 0.0
                elif line == -0.75:
                    val = 1.0 if goal_diff >= 2 else (0.5 if goal_diff == 1 else 0.0)
                elif line == -1.0:
                    val = 1.0 if goal_diff >= 2 else 0.0
                suggested_lines[f"{prefix} {line}"] = val

            asian_handicap = {
                "label": f"{prefix} -0.5" if goal_diff > 0 else "Level (0)",
                "lines": suggested_lines,
                "favored_team": prefix,
            }

            # Team goals
            team_goals = {
                "home": {
                    "over_0_5": 1.0 if home_score > 0.5 else 0.0,
                    "over_1_5": 1.0 if home_score > 1.5 else 0.0,
                    "over_2_5": 1.0 if home_score > 2.5 else 0.0
                },
                "away": {
                    "over_0_5": 1.0 if away_score > 0.5 else 0.0,
                    "over_1_5": 1.0 if away_score > 1.5 else 0.0,
                    "over_2_5": 1.0 if away_score > 2.5 else 0.0
                }
            }

            requested_scores = [
                "0-0", "1-0", "1-1", "2-0", "2-1", "2-2", "3-0", "3-1", "3-2", "3-3", "4-0", "4-1", "4-2", "4-3", "4-4"
            ]
            prob_matrix = {score: (1.0 if score == most_likely_score else 0.0) for score in requested_scores}

            # Normalize probabilities to sum exactly to 1
            norm_home, norm_draw, norm_away = ModelService.normalize_1x2_probs(
                prob_home, prob_draw, prob_away
            )
            return {
                "home_team": home.name,
                "away_team": away.name,
                "generated_at": now.isoformat(),
                "is_actual_result": True,
                # 1X2 predictions
                "outcome": {
                    "home_win_probability": norm_home,
                    "draw_probability": norm_draw,
                    "away_win_probability": norm_away,
                    "predicted_result": predicted_result,
                    "confidence": 1.0,
                    "confidence_level": "Very High",
                },
                # Goals (actual score used as xG for completed matches)
                "goals": {
                    "expected_home_goals": float(home_score),
                    "expected_away_goals": float(away_score),
                    "total_expected_goals": float(total_goals),
                },
                # Betting markets
                "markets": {
                    "over_under": over_under,
                    "btts": btts,
                    "most_likely_score": most_likely_score,
                    "top_5_scorelines": top_5_scorelines,
                    "asian_handicap": asian_handicap,
                    "team_goals": team_goals,
                    "probability_matrix": prob_matrix,
                    "clean_sheet": {
                        "home_clean_sheet": 1.0 if away_score == 0 else 0.0,
                        "away_clean_sheet": 1.0 if home_score == 0 else 0.0,
                    },
                },
                # Backwards compatible model versions (kept at top level)
                "model_versions": {
                    "wc_model": "actual_result_override",
                    "goal_model": "actual_result_override",
                },
                # New detailed engine metadata (grouped)
                "prediction_engine": "Actual Result Override",
                "winner_engine": "Actual Result Override",
                "goal_engine": "Actual Result Override",
                "market_engine": "Actual Result Override",
                # Betting market predictions (if models loaded, otherwise Poisson fallback)
                "betting_markets": self._predict_betting_markets(
                    db, home.id, away.id, now, competition_code, match_record, {
                        "asian_handicap": asian_handicap,
                        "over_under": over_under,
                        "btts": btts,
                        "clean_sheet": {
                            "home_clean_sheet": 1.0 if away_score == 0 else 0.0,
                            "away_clean_sheet": 1.0 if home_score == 0 else 0.0,
                        },
                        "most_likely_score": most_likely_score,
                    }
                ),
            }

        result_goals = self.predict_goals(db, home.id, away.id, now, competition_code, match_record)
        
        # Get outcome from Poisson probabilities for full consistency!
        outcome_probs = result_goals["outcome_probabilities"]
        home_win_p_raw = outcome_probs["home_win_probability"]
        draw_p_raw = outcome_probs["draw_probability"]
        away_win_p_raw = outcome_probs["away_win_probability"]
        
        # Normalize probabilities to sum exactly to 1
        home_win_p, draw_p, away_win_p = ModelService.normalize_1x2_probs(
            home_win_p_raw, draw_p_raw, away_win_p_raw
        )
        
        max_p = max(home_win_p, draw_p, away_win_p)
        if max_p == home_win_p:
            predicted_result = "HOME_WIN"
        elif max_p == away_win_p:
            predicted_result = "AWAY_WIN"
        else:
            predicted_result = "DRAW"
        
        # Calculate new confidence
        confidence, confidence_level = ModelService.calculate_confidence(
            home_win_p, draw_p, away_win_p
        )
        
        return {
            "home_team": home.name,
            "away_team": away.name,
            "generated_at": now.isoformat(),
            # 1X2 predictions
            "outcome": {
                "home_win_probability": home_win_p,
                "draw_probability": draw_p,
                "away_win_probability": away_win_p,
                "predicted_result": predicted_result,
                "confidence": confidence,
                "confidence_level": confidence_level,
            },
            # Goals
            "goals": {
                "expected_home_goals": result_goals["expected_home_goals"],
                "expected_away_goals": result_goals["expected_away_goals"],
                "total_expected_goals": result_goals["total_expected_goals"],
            },
            # Markets (now includes clean_sheet and O/U 0.5–4.5)
            "markets": {
                "over_under": result_goals["over_under"],
                "btts": result_goals["btts"],
                "most_likely_score": result_goals["most_likely_score"],
                "top_5_scorelines": result_goals["top_5_scorelines"],
                "asian_handicap": result_goals["asian_handicap"],
                "team_goals": result_goals["team_goals"],
                "probability_matrix": result_goals["probability_matrix"],
                "clean_sheet": result_goals["clean_sheet"],
            },
            # Backwards compatible model versions (kept at top level)
            "model_versions": {
                "wc_model": result_goals["model_version"],
                "goal_model": result_goals["model_version"],
            },
            # New detailed engine metadata
            "prediction_engine": "Hybrid Prediction Engine",
            "winner_engine": POISSON_ENGINE_VERSION,
            "goal_engine": result_goals["model_version"],
            "market_engine": "Hybrid Market Engine",
            # Betting market predictions (if models loaded, otherwise Poisson fallback)
            "betting_markets": self._predict_betting_markets(
                db, home.id, away.id, now, competition_code, match_record, result_goals
            ),
        }

    # ── Betting market predictions with fallback ─────────────────────────────────
    def _predict_betting_markets(
        self, db, home_team_id: int, away_team_id: int, match_date,
        competition_code: str, match, goal_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict betting markets using dedicated models if available,
        otherwise fall back to Poisson-based predictions from goal model.
        """
        goal_result = goal_result or {}
        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code, match=match)
        
        result = {
            "asian_handicap": None,
            "asian_total": None,
            "btts": None,
            "clean_sheet": None,
            "correct_score": None,
        }
        
        # Try to use dedicated betting market models
        for market_name in ["asian_handicap", "asian_total", "btts", "clean_sheet", "correct_score"]:
            if market_name in self._betting_models:
                try:
                    bundle = self._betting_models[market_name]
                    model = bundle["model"]
                    feature_names = bundle["features"]
                    
                    feature_vec = [float(features.get(f, 0.0)) for f in feature_names]
                    df_input = __import__("pandas").DataFrame([feature_vec], columns=feature_names)
                    
                    probs = model.predict_proba(df_input)[0]
                    
                    if market_name == "asian_handicap":
                        # Use Poisson structure for consistency with frontend expectations
                        poisson_handicap = goal_result.get("asian_handicap", {})
                        result["asian_handicap"] = {
                            "label": poisson_handicap.get("label", "Level (0)"),
                            "lines": poisson_handicap.get("lines", {}),
                            "favored_team": poisson_handicap.get("favored_team", "Home"),
                            "source": "ml_model",
                            "model_version": bundle.get("version", "unknown"),
                        }
                    elif market_name == "asian_total":
                        result["asian_total"] = {
                            "over_2_5_prob": float(probs[1]) if len(probs) > 1 else 0.5,
                            "source": "ml_model",
                            "model_version": bundle.get("version", "unknown"),
                        }
                    elif market_name == "btts":
                        result["btts"] = {
                            "yes_prob": float(probs[1]) if len(probs) > 1 else 0.5,
                            "source": "ml_model",
                            "model_version": bundle.get("version", "unknown"),
                        }
                    elif market_name == "clean_sheet":
                        result["clean_sheet"] = {
                            "home_clean_sheet_prob": float(probs[1]) if len(probs) > 1 else 0.5,
                            "source": "ml_model",
                            "model_version": bundle.get("version", "unknown"),
                        }
                    elif market_name == "correct_score":
                        result["correct_score"] = {
                            "probabilities": [float(p) for p in probs],
                            "source": "ml_model",
                            "model_version": bundle.get("version", "unknown"),
                        }
                except Exception as e:
                    logger.warning(f"Failed to use {market_name} model: {e}")
        
        # Fallback to Poisson-based predictions for any missing markets
        if result["asian_handicap"] is None:
            # Use the full Poisson handicap structure from goal_result
            poisson_handicap = goal_result.get("asian_handicap", {})
            result["asian_handicap"] = {
                "label": poisson_handicap.get("label", "Level (0)"),
                "lines": poisson_handicap.get("lines", {}),
                "favored_team": poisson_handicap.get("favored_team", "Home"),
                "source": "poisson_fallback",
            }
            logger.info(f"[BETTING_MARKETS] Asian Handicap Poisson fallback: {result['asian_handicap']}")
        else:
            logger.info(f"[BETTING_MARKETS] Asian Handicap from ML model: {result['asian_handicap']}")
        
        # Ensure lines is never empty - generate from Poisson if needed
        if result["asian_handicap"] and isinstance(result["asian_handicap"], dict):
            if not result["asian_handicap"].get("lines") or len(result["asian_handicap"].get("lines", {})) == 0:
                logger.warning(f"[BETTING_MARKETS] Asian Handicap lines is empty, generating from Poisson")
                poisson_handicap = goal_result.get("asian_handicap", {})
                result["asian_handicap"]["lines"] = poisson_handicap.get("lines", {})
                result["asian_handicap"]["label"] = result["asian_handicap"].get("label", poisson_handicap.get("label", "Level (0)"))
                result["asian_handicap"]["favored_team"] = result["asian_handicap"].get("favored_team", poisson_handicap.get("favored_team", "Home"))
                logger.info(f"[BETTING_MARKETS] Generated lines from Poisson: {result['asian_handicap']['lines']}")
        
        if result["asian_total"] is None:
            ou_2_5 = goal_result.get("over_under", {}).get("2.5", {})
            result["asian_total"] = {
                "over_2_5_prob": ou_2_5.get("over", 0.5),
                "source": "poisson_fallback",
            }
        
        if result["btts"] is None:
            btts = goal_result.get("btts", {})
            result["btts"] = {
                "yes_prob": btts.get("yes", 0.5),
                "source": "poisson_fallback",
            }
        
        if result["clean_sheet"] is None:
            cs = goal_result.get("clean_sheet", {})
            result["clean_sheet"] = {
                "home_clean_sheet_prob": cs.get("home_clean_sheet", 0.5),
                "source": "poisson_fallback",
            }
        
        if result["correct_score"] is None:
            result["correct_score"] = {
                "most_likely_score": goal_result.get("most_likely_score", "1-1"),
                "source": "poisson_fallback",
            }
        
        logger.info(f"[BETTING_MARKETS] Final result: {result}")
        return result


# ── Module-level singleton ────────────────────────────────────────────────────
model_service = ModelService()

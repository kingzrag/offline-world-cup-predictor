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
import numpy as np
import xgboost as xgb
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Resolved paths ────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_MODELS_DIR = os.path.join(_ROOT, "models")

WC_MODEL_PATH   = os.path.join(_MODELS_DIR, "world_cup_predictor.pkl")
GOAL_MODEL_PATH = os.path.join(_MODELS_DIR, "goal_predictor.pkl")


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

        self._initialized = True
        logger.info("ModelService: both models ready.")

    # ── Health status ─────────────────────────────────────────────────────────
    @property
    def is_ready(self) -> bool:
        return self._initialized

    @property
    def model_versions(self) -> Dict[str, str]:
        if not self._initialized:
            return {"wc_model": "not_loaded", "goal_model": "not_loaded"}
        return {
            "wc_model":   self._wc_bundle.get("version", "unknown"),
            "goal_model": self._goal_bundle.get("version", "unknown"),
        }

    # ── Internal: extract features ────────────────────────────────────────────
    def _get_features(self, db, home_team_id: int, away_team_id: int,
                      match_date, competition_code: str = "WC",
                      match_stage: Optional[str] = None) -> Dict[str, float]:
        from ml.features import extract_ml_features
        return extract_ml_features(
            db, home_team_id, away_team_id, match_date,
            competition_code=competition_code,
            match_stage=match_stage,
        )

    # ── 1X2 Prediction ────────────────────────────────────────────────────────
    def predict_1x2(self, db, home_team_id: int, away_team_id: int,
                    match_date=None, competition_code: str = "WC") -> Dict[str, Any]:
        """
        Returns Home Win / Draw / Away Win probabilities using world_cup_predictor.pkl.
        """
        if not self._initialized:
            raise RuntimeError("ModelService not initialised – call load_models() first.")

        match_date = match_date or datetime.now(timezone.utc)
        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code)

        wc_features: list = self._wc_bundle.get("features", [])
        model: xgb.XGBClassifier = self._wc_bundle["model"]

        feature_vec = [features.get(f, 0.0) for f in wc_features]
        df_input    = __import__("pandas").DataFrame([feature_vec], columns=wc_features)

        probs = model.predict_proba(df_input)[0]
        # Training label mapping: 0 = Away Win, 1 = Draw, 2 = Home Win
        prob_away, prob_draw, prob_home = float(probs[0]), float(probs[1]), float(probs[2])
        prob_home = round(prob_home, 4)
        prob_away = round(prob_away, 4)
        prob_draw = round(prob_draw, 4)

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
                      match_date=None, competition_code: str = "WC") -> Dict[str, Any]:
        """
        Returns expected goals + full betting market suite via Poisson engine.
        """
        if not self._initialized:
            raise RuntimeError("ModelService not initialised – call load_models() first.")

        match_date = match_date or datetime.now(timezone.utc)
        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code)

        goal_features: list = self._goal_bundle.get("features", [])
        home_model: xgb.XGBRegressor = self._goal_bundle["home_model"]
        away_model: xgb.XGBRegressor = self._goal_bundle["away_model"]

        feature_vec = np.array([[features.get(f, 0.0) for f in goal_features]])

        expected_home = max(0.0, float(home_model.predict(feature_vec)[0]))
        expected_away = max(0.0, float(away_model.predict(feature_vec)[0]))
        total_goals   = expected_home + expected_away

        # ── Poisson markets ───────────────────────────────────────────────────
        from services.poisson_engine import evaluate_poisson_engine
        poisson = evaluate_poisson_engine(expected_home, expected_away)

        ou   = poisson["over_under"]
        btts = poisson["btts"]

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
            # Over / Under
            "over_under": {
                "1.5": ou["1.5"],
                "2.5": ou["2.5"],
                "3.5": ou["3.5"],
            },
            # BTTS
            "btts": {
                "yes": btts["btts_yes"],
                "no":  btts["btts_no"],
            },
            # Correct score
            "most_likely_score":  poisson["most_likely_score"],
            "top_5_scorelines":   poisson["top_5_scorelines"],
            # Asian handicap
            "asian_handicap": {
                "label":       asian_handicap_label,
                "lines":       poisson["asian_handicap"]["suggested_lines"],
                "favored_team": poisson["asian_handicap"]["favored_team_prefix"],
            },
            # Team goals
            "team_goals":          poisson["team_goals"],
            # Full probability matrix
            "probability_matrix":  poisson["probability_matrix"],
            "model_version":       self._goal_bundle.get("version", "v1.0"),
        }

    # ── Combined full prediction ───────────────────────────────────────────────
    def predict(self, db, home_team_name: str, away_team_name: str,
                competition_code: str = "WC") -> Dict[str, Any]:
        """
        Full prediction combining 1X2 + goals + all markets.
        Resolves team names to IDs internally.

        Raises ValueError if either team is not found in the database.
        """
        from models import Team

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

        now = datetime.now(timezone.utc)

        result_1x2   = self.predict_1x2(db, home.id, away.id, now, competition_code)
        result_goals = self.predict_goals(db, home.id, away.id, now, competition_code)

        return {
            "home_team":  home.name,
            "away_team":  away.name,
            "generated_at": now.isoformat(),
            # 1X2
            "outcome": {
                "home_win_probability": result_1x2["home_win_probability"],
                "draw_probability":     result_1x2["draw_probability"],
                "away_win_probability": result_1x2["away_win_probability"],
                "predicted_result":     result_1x2["predicted_outcome"],
                "confidence":           result_1x2["confidence"],
            },
            # Goals
            "goals": {
                "expected_home_goals":  result_goals["expected_home_goals"],
                "expected_away_goals":  result_goals["expected_away_goals"],
                "total_expected_goals": result_goals["total_expected_goals"],
            },
            # Markets
            "markets": {
                "over_under":          result_goals["over_under"],
                "btts":                result_goals["btts"],
                "most_likely_score":   result_goals["most_likely_score"],
                "top_5_scorelines":    result_goals["top_5_scorelines"],
                "asian_handicap":      result_goals["asian_handicap"],
                "team_goals":          result_goals["team_goals"],
                "probability_matrix":  result_goals["probability_matrix"],
            },
            "model_versions": {
                "wc_model":   result_1x2["model_version"],
                "goal_model": result_goals["model_version"],
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
model_service = ModelService()

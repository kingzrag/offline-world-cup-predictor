import os
import math
import pandas as pd
from typing import Dict, Any

import xgboost as xgb

# Local imports
from .features import extract_ml_features


class FootballPredictor:
    """Machine Learning Prediction Engine using trained XGBoost model.

    The model predicts probabilities for three outcomes:
    0 = Away Win, 1 = Draw, 2 = Home Win.
    """

    def __init__(self, model_version: str = "v1.0"):
        self.model_version = model_version
        # Resolve model file path relative to this predictor module
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "models", "xgboost_model.json")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Trained XGBoost model not found at {model_path}. Run ml/train_model.py first."
            )
        # Load the XGBoost classifier
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)
        # Feature ordering must match training columns
        self.feature_order = [
            "elo_diff",
            "fifa_diff",
            "form_diff",
            "gs_diff",
            "gc_diff",
            "mv_diff",
            "inj_diff",
            "susp_diff",
            "home_adv",
            "h2h_factor",
        ]

    def predict_outcome(self, db, home_team_id: int, away_team_id: int, match_date, competition_code: str = "PL") -> Dict[str, Any]:
        """Compute outcome probabilities for a specific match.

        Args:
            db: SQLAlchemy session/connection.
            home_team_id: ID of the home team.
            away_team_id: ID of the away team.
            match_date: Date of the match (datetime).
            competition_code: Competition identifier (default "PL").

        Returns:
            Dictionary containing probabilities for HOME_WIN, AWAY_WIN, DRAW,
            the predicted outcome string, and model version.
        """
        # 1. Extract engineered features using existing feature module
        feature_dict = extract_ml_features(
            db, home_team_id, away_team_id, match_date, competition_code
        )
        # Ensure all expected keys exist; missing keys default to 0
        feature_vec = [feature_dict.get(key, 0.0) for key in self.feature_order]
        # 2. Create DataFrame for model prediction (single row)
        df = pd.DataFrame([feature_vec], columns=self.feature_order)
        # 3. Predict class probabilities
        probs = self.model.predict_proba(df)[0]  # shape (3,)
        # Mapping: index 0 -> Away Win, 1 -> Draw, 2 -> Home Win
        prob_away, prob_draw, prob_home = probs.tolist()
        # Round for readability
        prob_home = round(prob_home, 4)
        prob_away = round(prob_away, 4)
        prob_draw = round(prob_draw, 4)
        # 4. Determine predicted outcome (highest probability)
        max_prob = max(prob_home, prob_away, prob_draw)
        if max_prob == prob_home:
            outcome = "HOME_WIN"
        elif max_prob == prob_away:
            outcome = "AWAY_WIN"
        else:
            outcome = "DRAW"
        return {
            "home_probability": prob_home,
            "away_probability": prob_away,
            "draw_probability": prob_draw,
            "predicted_outcome": outcome,
            "model_version": self.model_version,
        }

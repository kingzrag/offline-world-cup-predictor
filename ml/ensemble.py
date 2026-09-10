"""
ml/ensemble.py
================
Multi-Method Prediction Ensemble & Calibration Engine.

Combines predictions from:
  1. Dixon-Coles Goal Engine  (model_id: "dixon_coles", weight: 0.5608)
  2. Direct Elo Probability   (model_id: "elo",         weight: 0.2842)
  3. XGBoost 1X2 Classifier   (model_id: "xgb_1x2",     weight: 0.1550)
  4. Pure Poisson Goal Engine (model_id: "poisson",     weight: 0.0000)

Applies a validation-fitted scikit-learn multinomial logistic calibrator
loaded from models/ensemble_calibrator.pkl.
"""

import os
import pickle
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_CALIBRATOR_PATH = os.path.join(_ROOT, "models", "ensemble_calibrator.pkl")


@dataclass
class ModelPrediction:
    model_id: str                # Canonical identifier: "dixon_coles", "elo", "xgb_1x2", "poisson"
    model_name: str              # Display name: "Dixon-Coles Model", "Direct Elo Model", etc.
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    expected_home_goals: Optional[float] = None
    expected_away_goals: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "home_win_probability": round(self.home_win_probability, 4),
            "draw_probability": round(self.draw_probability, 4),
            "away_win_probability": round(self.away_win_probability, 4),
        }
        if self.expected_home_goals is not None:
            res["expected_home_goals"] = round(self.expected_home_goals, 4)
        if self.expected_away_goals is not None:
            res["expected_away_goals"] = round(self.expected_away_goals, 4)
        if self.metadata:
            res["metadata"] = self.metadata
        return res


class EnsemblePredictor:
    """
    Production-grade Ensemble Predictor that combines individual ModelPredictions
    using exact canonical model_id matching and validation-fitted multinomial calibration.
    """

    DEFAULT_WEIGHTS = {
        "dixon_coles": 0.5608,
        "elo": 0.2842,
        "xgb_1x2": 0.1550,
        "poisson": 0.0000,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        use_calibration: bool = True,
        calibrator_path: str = _CALIBRATOR_PATH
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.use_calibration = use_calibration
        self.calibrator = None
        self._load_calibrator(calibrator_path)

    def _load_calibrator(self, calibrator_path: str) -> None:
        """Loads serialized scikit-learn multinomial logistic calibrator artifact."""
        if os.path.exists(calibrator_path):
            try:
                with open(calibrator_path, "rb") as f:
                    bundle = pickle.load(f)
                self.calibrator = bundle.get("calibrator")
                logger.info(f"EnsemblePredictor: loaded calibrator artifact from {calibrator_path}")
            except Exception as e:
                logger.warning(f"EnsemblePredictor: failed to load calibrator artifact: {e}")
        else:
            logger.info(f"EnsemblePredictor: calibrator artifact not found at {calibrator_path} (will use raw probabilities)")

    @staticmethod
    def normalize_probs(home_p: float, draw_p: float, away_p: float) -> Tuple[float, float, float]:
        """Ensures 1X2 probabilities sum to exactly 1.0, absorbing rounding diff."""
        h = round(home_p, 4)
        d = round(draw_p, 4)
        a = round(away_p, 4)
        tot = h + d + a
        if tot == 1.0:
            return h, d, a
        diff = 1.0 - tot
        if h >= d and h >= a:
            return round(h + diff, 4), d, a
        elif d >= h and d >= a:
            return h, round(d + diff, 4), a
        else:
            return h, d, round(a + diff, 4)

    @staticmethod
    def calculate_confidence(home_p: float, draw_p: float, away_p: float) -> Tuple[float, str]:
        """Calculates margin-based confidence score and level."""
        probs = sorted([home_p, draw_p, away_p], reverse=True)
        margin = probs[0] - probs[1]
        score = round(margin, 4)
        if score >= 0.50:
            level = "Very High"
        elif score >= 0.20:
            level = "High"
        elif score >= 0.05:
            level = "Medium"
        else:
            level = "Low"
        return score, level

    def calibrate_probs(self, home_p: float, draw_p: float, away_p: float) -> Tuple[float, float, float]:
        """
        Applies validation-fitted multinomial logistic calibrator to raw ensemble probabilities.
        """
        if not self.use_calibration or self.calibrator is None:
            return self.normalize_probs(home_p, draw_p, away_p)

        try:
            # Calibrator expects 2D array of shape (1, 3) in order [away, draw, home] (labels 0, 1, 2)
            raw_vec = np.array([[away_p, draw_p, home_p]])
            cal_probs = self.calibrator.predict_proba(raw_vec)[0] # Array of shape (3,) -> [p_away, p_draw, p_home]
            cal_away, cal_draw, cal_home = float(cal_probs[0]), float(cal_probs[1]), float(cal_probs[2])
            return self.normalize_probs(cal_home, cal_draw, cal_away)
        except Exception as e:
            logger.warning(f"EnsemblePredictor: calibration application failed ({e}), falling back to raw probs")
            return self.normalize_probs(home_p, draw_p, away_p)

    def combine(self, predictions: List[ModelPrediction], allow_missing: bool = False) -> Dict[str, Any]:
        """
        Combines individual ModelPrediction objects using canonical model_id lookup.

        Args:
            predictions: List of ModelPrediction objects
            allow_missing: If True, allows missing expected models without raising ValueError

        Returns:
            Dictionary containing outcome, goals, ensemble_weights, individual_models breakdown
        """
        pred_map = {p.model_id: p for p in predictions}

        # Check for missing non-zero weight models
        missing_models = [m_id for m_id, w in self.weights.items() if w > 0.0 and m_id not in pred_map]
        if missing_models:
            msg = f"EnsemblePredictor: missing critical prediction models: {missing_models}"
            logger.error(msg)
            if not allow_missing:
                raise ValueError(msg)

        raw_home = 0.0
        raw_draw = 0.0
        raw_away = 0.0
        total_weight = 0.0

        for model_id, weight in self.weights.items():
            if weight <= 0.0:
                continue
            pred = pred_map.get(model_id)
            if pred:
                raw_home += weight * pred.home_win_probability
                raw_draw += weight * pred.draw_probability
                raw_away += weight * pred.away_win_probability
                total_weight += weight

        if total_weight > 0.0:
            raw_home /= total_weight
            raw_draw /= total_weight
            raw_away /= total_weight
        else:
            # Equal average fallback if total_weight is zero
            raw_home = np.mean([p.home_win_probability for p in predictions])
            raw_draw = np.mean([p.draw_probability for p in predictions])
            raw_away = np.mean([p.away_win_probability for p in predictions])

        # Raw pre-calibration probabilities
        raw_home_norm, raw_draw_norm, raw_away_norm = self.normalize_probs(raw_home, raw_draw, raw_away)

        # Apply calibration
        fin_home, fin_draw, fin_away = self.calibrate_probs(raw_home_norm, raw_draw_norm, raw_away_norm)

        # Determine predicted result
        max_p = max(fin_home, fin_draw, fin_away)
        if max_p == fin_home:
            predicted_result = "HOME_WIN"
        elif max_p == fin_away:
            predicted_result = "AWAY_WIN"
        else:
            predicted_result = "DRAW"

        confidence, confidence_level = self.calculate_confidence(fin_home, fin_draw, fin_away)

        # Extract goals from predictions
        h_xg = None
        a_xg = None
        for p in predictions:
            if p.expected_home_goals is not None and p.expected_away_goals is not None:
                h_xg = p.expected_home_goals
                a_xg = p.expected_away_goals
                break

        return {
            "outcome": {
                "home_win_probability": fin_home,
                "draw_probability": fin_draw,
                "away_win_probability": fin_away,
                "predicted_result": predicted_result,
                "confidence": confidence,
                "confidence_level": confidence_level,
            },
            "raw_uncalibrated_outcome": {
                "home_win_probability": raw_home_norm,
                "draw_probability": raw_draw_norm,
                "away_win_probability": raw_away_norm,
            },
            "goals": {
                "expected_home_goals": h_xg,
                "expected_away_goals": a_xg,
                "total_expected_goals": round(h_xg + a_xg, 4) if (h_xg is not None and a_xg is not None) else None,
            },
            "ensemble_weights": self.weights,
            "is_calibrated": self.use_calibration and (self.calibrator is not None),
            "individual_models": {p.model_name: p.to_dict() for p in predictions},
        }


# Module singleton instance
ensemble_predictor = EnsemblePredictor()

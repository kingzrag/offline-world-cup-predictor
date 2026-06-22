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

        # ── Resolve team names for logging ───────────────────────────────────
        from models import Team as _Team
        _home = db.query(_Team).filter_by(id=home_team_id).first()
        _away = db.query(_Team).filter_by(id=away_team_id).first()
        _home_name = _home.name if _home else str(home_team_id)
        _away_name = _away.name if _away else str(away_team_id)
        logger.info(f"[predict_1x2] {_home_name} vs {_away_name} [{competition_code}]")

        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code)

        wc_features: list = self._wc_bundle.get("features", [])
        model: xgb.XGBClassifier = self._wc_bundle["model"]

        feature_vec = [features.get(f, 0.0) for f in wc_features]

        # ── Log full feature dict and final vector ────────────────────────────
        logger.info(f"[predict_1x2] Extracted features for {_home_name} vs {_away_name}:")
        for k, v in features.items():
            logger.info(f"  {k:<40} = {v}")
        logger.info(f"[predict_1x2] Feature vector ({len(feature_vec)} values): {[round(v, 4) for v in feature_vec]}")

        df_input    = __import__("pandas").DataFrame([feature_vec], columns=wc_features)

        probs = model.predict_proba(df_input)[0]
        # Training label mapping: 0 = Away Win, 1 = Draw, 2 = Home Win
        prob_away, prob_draw, prob_home = float(probs[0]), float(probs[1]), float(probs[2])
        logger.info(
            f"[predict_1x2] Raw model probs for {_home_name} vs {_away_name}: "
            f"home={prob_home:.4f}  draw={prob_draw:.4f}  away={prob_away:.4f}"
        )
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

        # ── Resolve team names for logging ───────────────────────────────────
        from models import Team as _Team
        _home = db.query(_Team).filter_by(id=home_team_id).first()
        _away = db.query(_Team).filter_by(id=away_team_id).first()
        _home_name = _home.name if _home else str(home_team_id)
        _away_name = _away.name if _away else str(away_team_id)
        logger.info(f"[predict_goals] {_home_name} vs {_away_name} [{competition_code}]")

        features = self._get_features(db, home_team_id, away_team_id, match_date, competition_code)

        goal_features: list = self._goal_bundle.get("features", [])
        home_model: xgb.XGBRegressor = self._goal_bundle["home_model"]
        away_model: xgb.XGBRegressor = self._goal_bundle["away_model"]

        feature_vals = [features.get(f, 0.0) for f in goal_features]

        # ── Log full feature dict and final vector ────────────────────────────
        logger.info(f"[predict_goals] Extracted features for {_home_name} vs {_away_name}:")
        for k, v in features.items():
            logger.info(f"  {k:<40} = {v}")
        logger.info(f"[predict_goals] Feature vector ({len(feature_vals)} values) for goal models: {[round(v, 4) if isinstance(v, (int, float)) else v for v in feature_vals]}")

        # Check for NaN or zero-only vectors
        import math
        has_nan = any(isinstance(v, float) and math.isnan(v) for v in feature_vals)
        all_zeros = all(v == 0.0 for v in feature_vals)
        if has_nan:
            logger.warning(f"[predict_goals] NaN detected in feature vector for {_home_name} vs {_away_name}!")
        if all_zeros:
            logger.warning(f"[predict_goals] Zero-only feature vector detected for {_home_name} vs {_away_name}!")

        feature_vec = np.array([feature_vals])

        expected_home = max(0.0, float(home_model.predict(feature_vec)[0]))
        expected_away = max(0.0, float(away_model.predict(feature_vec)[0]))
        total_goals   = expected_home + expected_away

        logger.info(f"[predict_goals] Expected Goals predicted: {_home_name}={expected_home:.4f}, {_away_name}={expected_away:.4f}, Total={total_goals:.4f}")

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
            # Over / Under (0.5 – 4.5)
            "over_under": poisson["over_under"],
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
                "label":        asian_handicap_label,
                "lines":        poisson["asian_handicap"]["suggested_lines"],
                "favored_team": poisson["asian_handicap"]["favored_team_prefix"],
            },
            # Team goals
            "team_goals":          poisson["team_goals"],
            # Clean sheet (Poisson P(0) = e^(-lambda))
            "clean_sheet":         poisson["clean_sheet"],
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

            return {
                "home_team":  home.name,
                "away_team":  away.name,
                "generated_at": now.isoformat(),
                "is_actual_result": True,
                # 1X2
                "outcome": {
                    "home_win_probability": prob_home,
                    "draw_probability":     prob_draw,
                    "away_win_probability": prob_away,
                    "predicted_result":     predicted_result,
                    "confidence":           1.0,
                },
                # Goals (actual score used as xG for completed matches)
                "goals": {
                    "expected_home_goals":  float(home_score),
                    "expected_away_goals":  float(away_score),
                    "total_expected_goals": float(total_goals),
                },
                # Markets
                "markets": {
                    "over_under":          over_under,
                    "btts":                btts,
                    "most_likely_score":   most_likely_score,
                    "top_5_scorelines":    top_5_scorelines,
                    "asian_handicap":      asian_handicap,
                    "team_goals":          team_goals,
                    "probability_matrix":  prob_matrix,
                    # Clean sheet — binary for completed matches
                    "clean_sheet": {
                        "home_clean_sheet": 1.0 if away_score == 0 else 0.0,
                        "away_clean_sheet": 1.0 if home_score == 0 else 0.0,
                    },
                },
                "model_versions": {
                    "wc_model":   "actual_result_override",
                    "goal_model": "actual_result_override",
                },
            }

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
            # Markets (now includes clean_sheet and O/U 0.5–4.5)
            "markets": {
                "over_under":          result_goals["over_under"],
                "btts":                result_goals["btts"],
                "most_likely_score":   result_goals["most_likely_score"],
                "top_5_scorelines":    result_goals["top_5_scorelines"],
                "asian_handicap":      result_goals["asian_handicap"],
                "team_goals":          result_goals["team_goals"],
                "probability_matrix":  result_goals["probability_matrix"],
                "clean_sheet":         result_goals["clean_sheet"],
            },
            "model_versions": {
                "wc_model":   result_1x2["model_version"],
                "goal_model": result_goals["model_version"],
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
model_service = ModelService()

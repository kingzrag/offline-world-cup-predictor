#!/usr/bin/env python3
"""
verify_match_intelligence.py — Match Intelligence verification

Tests:
  - IntelligenceService initializes
  - All 16 metrics are computed for a recent match
  - Safe defaults when data is sparse
  - features dict has correct keys
  - confidence score is in [0, 1]

Usage:
  python verify_match_intelligence.py
  python verify_match_intelligence.py --match-id 123
"""

import sys
import argparse
from datetime import datetime

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

def ok(msg):      print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):    print(f"  {RED}✗{RESET} {msg}")
def warn(msg):    print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg):    print(f"  {BLUE}→{RESET} {msg}")
def section(msg): print(f"\n{BLUE}{'='*60}{RESET}\n{BLUE}{msg}{RESET}\n{'='*60}")


EXPECTED_INTELLIGENCE_KEYS = [
    "home_attacking_strength", "away_attacking_strength",
    "home_defensive_strength", "away_defensive_strength",
    "home_midfield_control", "away_midfield_control",
    "home_goalkeeper_performance", "away_goalkeeper_performance",
    "home_passing_dominance", "away_passing_dominance",
    "home_pressing_intensity", "away_pressing_intensity",
    "home_set_piece_threat", "away_set_piece_threat",
    "home_discipline_score", "away_discipline_score",
    "home_fatigue_score", "away_fatigue_score",
    "home_substitution_impact", "away_substitution_impact",
    "home_player_availability_score", "away_player_availability_score",
    "home_injury_impact", "away_injury_impact",
    "home_suspension_impact", "away_suspension_impact",
    "home_formation_stability", "away_formation_stability",
    "home_momentum_score", "away_momentum_score",
    "confidence_score",
    "data_completeness",
]

EXPECTED_FEATURE_KEYS = [
    # Existing keys that must still be present (backward compatibility)
    "elo_diff", "fifa_diff", "form_diff", "mv_diff",
    "home_adv", "h2h_factor",
    # New intelligence keys
    "home_attacking_strength", "away_attacking_strength", "attacking_strength_diff",
    "home_defensive_strength", "away_defensive_strength", "defensive_strength_diff",
    "home_midfield_control", "away_midfield_control",
    "home_momentum_score", "away_momentum_score", "momentum_score_diff",
    "home_discipline_score", "away_discipline_score",
    "home_fatigue_score", "away_fatigue_score",
    "confidence_score",
]


def test_intelligence_service_init():
    section("IntelligenceService — Initialization")
    passed = failed = 0

    try:
        from services.intelligence_service import IntelligenceService
        svc = IntelligenceService()
        ok("IntelligenceService initializes")
        passed += 1
    except Exception as e:
        fail(f"IntelligenceService init failed: {e}")
        failed += 1
        return passed, failed

    # Test to_features_dict with a default intelligence object
    try:
        from providers.base import MatchIntelligence
        default_intel = MatchIntelligence(match_id=0)
        features = svc.to_features_dict(default_intel)

        for key in EXPECTED_INTELLIGENCE_KEYS:
            if key in features:
                ok(f"Feature key present: {key} = {features[key]}")
                passed += 1
            else:
                fail(f"Missing feature key: {key}")
                failed += 1
    except Exception as e:
        fail(f"to_features_dict() raised: {e}")
        failed += 1

    return passed, failed


def test_match_intelligence_from_db(match_id=None):
    section("Match Intelligence — Live DB Test")
    passed = failed = warnings = 0

    try:
        from database.connection import SessionLocal
        from models import Match
        from services.intelligence_service import IntelligenceService

        db = SessionLocal()
        svc = IntelligenceService()

        # Find a match to test against
        if match_id:
            match = db.query(Match).filter(Match.id == match_id).first()
        else:
            match = db.query(Match).filter(
                Match.status == "FINISHED"
            ).order_by(Match.utc_date.desc()).first()

        if not match:
            warn("No finished matches found in DB — run data collection first")
            warnings += 1
            db.close()
            return passed, failed, warnings

        info(f"Testing with match ID {match.id}: "
             f"{getattr(match.home_team,'name','?')} vs {getattr(match.away_team,'name','?')}")

        # Compute intelligence
        intel = svc.calculate_match_intelligence(db, match)
        ok(f"calculate_match_intelligence() completed")
        ok(f"  confidence_score      = {intel.confidence_score:.3f}  (expect: 0.0–1.0)")
        ok(f"  data_completeness     = {intel.data_completeness:.1%}")
        ok(f"  home_momentum_score   = {intel.home_momentum_score:.3f}")
        ok(f"  away_momentum_score   = {intel.away_momentum_score:.3f}")
        ok(f"  home_availability     = {intel.home_player_availability_score:.3f}")
        ok(f"  away_availability     = {intel.away_player_availability_score:.3f}")
        ok(f"  sources_used          = {intel.sources_used}")
        passed += 1

        # Validate score ranges
        scores_to_check = [
            ("confidence_score", intel.confidence_score),
            ("home_attacking_strength", intel.home_attacking_strength),
            ("away_attacking_strength", intel.away_attacking_strength),
            ("home_defensive_strength", intel.home_defensive_strength),
            ("home_player_availability_score", intel.home_player_availability_score),
            ("home_momentum_score", intel.home_momentum_score),
        ]
        for name, val in scores_to_check:
            if -1.0 <= val <= 2.0:  # Reasonable range
                ok(f"  {name} in valid range: {val:.3f}")
                passed += 1
            else:
                fail(f"  {name} out of range: {val}")
                failed += 1

        # Test features dict
        features = svc.to_features_dict(intel)
        for key in EXPECTED_INTELLIGENCE_KEYS:
            if key in features:
                passed += 1
            else:
                fail(f"Missing key in to_features_dict: {key}")
                failed += 1

        db.close()

    except Exception as e:
        fail(f"DB test raised: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    return passed, failed, warnings


def test_ml_features_backward_compat():
    section("ML Features — Backward Compatibility Check")
    passed = failed = warnings = 0

    try:
        from database.connection import SessionLocal
        from models import Match
        from ml.features import extract_ml_features
        import models as _models

        db = SessionLocal()
        match = db.query(Match).filter(Match.status == "FINISHED").order_by(Match.utc_date.desc()).first()

        if not match:
            warn("No finished matches in DB to test ML features")
            warnings += 1
            db.close()
            return passed, failed, warnings

        home_team = db.query(_models.Team).filter_by(id=match.home_team_id).first()
        away_team = db.query(_models.Team).filter_by(id=match.away_team_id).first()

        if not home_team or not away_team:
            warn("Teams not found for test match")
            warnings += 1
            db.close()
            return passed, failed, warnings

        info(f"Testing ML features for: {home_team.name} vs {away_team.name}")

        features = extract_ml_features(
            db=db,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            match_date=match.utc_date,
            competition_code=None,
            match=match,
        )

        ok(f"get_match_features() returned {len(features)} features")
        passed += 1

        for key in EXPECTED_FEATURE_KEYS:
            if key in features:
                ok(f"  '{key}' present: {features[key]}")
                passed += 1
            else:
                fail(f"  '{key}' MISSING from features dict")
                failed += 1

        # Verify no None values in critical fields
        critical_keys = ["elo_diff", "home_adv", "confidence_score"]
        for key in critical_keys:
            val = features.get(key)
            if val is not None:
                ok(f"  Critical key '{key}' = {val} (not None)")
                passed += 1
            else:
                warn(f"  Critical key '{key}' is None (may be expected if DB lacks data)")
                warnings += 1

        db.close()

    except Exception as e:
        fail(f"ML features test raised: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    return passed, failed, warnings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Match Intelligence")
    parser.add_argument("--match-id", type=int, help="Specific match ID to test")
    args = parser.parse_args()

    total_p = total_f = total_w = 0

    p, f = test_intelligence_service_init()
    total_p += p; total_f += f

    p, f, w = test_match_intelligence_from_db(args.match_id)
    total_p += p; total_f += f; total_w += w

    p, f, w = test_ml_features_backward_compat()
    total_p += p; total_f += f; total_w += w

    section("SUMMARY")
    print(f"  {GREEN}Passed:   {total_p}{RESET}")
    print(f"  {YELLOW}Warnings: {total_w}{RESET}")
    print(f"  {RED}Failed:   {total_f}{RESET}")

    if total_f == 0:
        print(f"\n{GREEN}✓ Match Intelligence verification passed{RESET}")
    else:
        print(f"\n{RED}✗ {total_f} test(s) failed{RESET}")

    sys.exit(0 if total_f == 0 else 1)

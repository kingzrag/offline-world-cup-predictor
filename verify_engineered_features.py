#!/usr/bin/env python3
"""
Print engineered ML-only intelligence features for one real international match.

Shows:
- raw inputs
- calculated feature value
- contributing source providers
"""

from __future__ import annotations

import argparse
from pprint import pformat

from sqlalchemy import desc

from database.connection import SessionLocal
from models import (
    Competition,
    Match,
    MatchLineup,
    MatchStatistic,
    PlayerMatchPerformance,
)
from services.intelligence_service import IntelligenceService

INTERNATIONAL_CODES = {
    "WC",
    "EC",
    "CA",
    "UNL",
    "WWC",
    "OLY",
    "WCQ",
    "WCQA",
    "WCQC",
    "WCQE",
    "AFCON",
    "ASIAN",
    "CONCACAF",
    "GC",
}


def pick_match(db, match_id: int | None) -> Match | None:
    if match_id:
        return db.query(Match).filter(Match.id == match_id).first()

    return (
        db.query(Match)
        .join(Competition, Competition.id == Match.competition_id)
        .outerjoin(MatchStatistic, MatchStatistic.match_id == Match.id)
        .outerjoin(PlayerMatchPerformance, PlayerMatchPerformance.match_id == Match.id)
        .outerjoin(MatchLineup, MatchLineup.match_id == Match.id)
        .filter(Match.status == "FINISHED", Competition.code.in_(INTERNATIONAL_CODES))
        .group_by(Match.id)
        .order_by(desc(Match.statsbomb_id), desc(Match.utc_date))
        .first()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify engineered ML features")
    parser.add_argument("--match-id", type=int, help="Specific match ID to inspect")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        match = pick_match(db, args.match_id)
        if not match:
            print("No suitable international match found in the database.")
            return 1

        svc = IntelligenceService()
        intel = svc.calculate_match_intelligence(db, match)
        audit = svc.explain_engineered_features(db, match)

        print("=" * 100)
        print("ENGINEERED FEATURE VERIFICATION")
        print("=" * 100)
        print(f"Match ID:   {audit['match_id']}")
        print(f"Fixture:    {audit['fixture']}")
        print(f"Date:       {match.utc_date}")
        print(f"Confidence: {intel.confidence_score:.3f}")
        print(f"Completeness: {intel.data_completeness:.1%}")
        print()

        for feature_name, feature_payload in audit["features"].items():
            print(f"## {feature_name}")
            for side in ("home", "away"):
                team_payload = feature_payload[side]
                print(f"- {side.upper()} ({team_payload['team']})")
                print(f"  value:      {team_payload['value']}")
                print(f"  available:  {team_payload['available']}")
                print(f"  providers:  {', '.join(team_payload['providers']) or 'None'}")
                print("  raw_inputs:")
                formatted = pformat(team_payload["raw_inputs"], sort_dicts=False)
                for line in formatted.splitlines():
                    print(f"    {line}")
            print(f"- DIFF: {feature_payload['diff']}")
            print()

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

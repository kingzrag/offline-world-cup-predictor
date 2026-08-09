"""
ml/compute_club_elo.py

STEP 6B — Phase 4: Historical Club Elo Computation

Computes TEMPORAL ELO ratings for all club teams from domestic
league historical match data in the PostgreSQL database.

Rules:
- Elo is initialized at 1500 for all new clubs.
- After each match, both teams' Elo ratings update using the
  standard K-factor formula.
- Matches are processed in strict chronological order.
- For each training match, the stored Elo represents the team's
  rating BEFORE that match (no future leakage).
- Results are written to a separate table:
    ml/club_historical_elo.json
  This is used by the training dataset builder (NOT the live
  production TeamElo table — do not overwrite production Elo).

Formula:
    E_home = 1 / (1 + 10^((R_away - R_home) / 400))
    E_away = 1 - E_home
    S_home = 1 (win), 0.5 (draw), 0 (loss)
    R_new = R_old + K * (S - E)

K-factor strategy:
    - Default K = 32 (standard)
    - Promotion-era teams (only 1 season of data): K = 40 (settle faster)
    - Teams with 100+ matches: K = 24 (stable)
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from models import Match, Competition, Team
from sqlalchemy import or_

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("club_elo")

# ── Configuration ──────────────────────────────────────────────────────────────
TARGET_COMPETITIONS = ["PL", "PD", "SA", "BL1", "FL1", "DED", "BSA", "CL"]
INITIAL_ELO = 1500
K_DEFAULT = 32
K_LOW_HISTORY = 40   # < 20 matches played
K_HIGH_HISTORY = 24  # > 100 matches played
OUTPUT_PATH = Path(__file__).parent / "club_historical_elo.json"


def expected_score(r_a: float, r_b: float) -> float:
    """Expected score for team A against team B."""
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))


def k_factor(matches_played: int) -> float:
    if matches_played < 20:
        return K_LOW_HISTORY
    elif matches_played > 100:
        return K_HIGH_HISTORY
    return K_DEFAULT


def compute_club_elo() -> dict:
    """
    Compute historical Elo for all clubs in target competitions.
    
    Returns dict: {
        team_id: {
            "name": str,
            "final_elo": float,
            "match_history": [
                {"match_id": int, "date": str, "elo_before": float, "elo_after": float, ...}
            ]
        }
    }
    """
    db = SessionLocal()
    try:
        # Load canonical team ID map if available
        canon_map_path = Path(__file__).parent / "canonical_team_id_map.json"
        canonical_map = {}
        if canon_map_path.exists():
            raw = json.loads(canon_map_path.read_text())
            canonical_map = {int(k): int(v) for k, v in raw.items()}
            logger.info(f"Loaded canonical team map: {len(canonical_map)} aliases")

        def canonical_id(tid: int) -> int:
            return canonical_map.get(tid, tid)

        # Get all competition IDs
        comp_ids = []
        for code in TARGET_COMPETITIONS:
            c = db.query(Competition).filter_by(code=code).first()
            if c:
                comp_ids.append(c.id)

        # Load ALL finished matches across target competitions, sorted chronologically
        all_matches = (
            db.query(Match)
            .filter(
                Match.competition_id.in_(comp_ids),
                Match.status == "FINISHED",
                Match.home_score.isnot(None),
                Match.away_score.isnot(None),
            )
            .order_by(Match.utc_date.asc())
            .all()
        )
        logger.info(f"Processing {len(all_matches)} finished matches across {len(comp_ids)} competitions")

        # State: current Elo per canonical team_id
        elo: dict[int, float] = defaultdict(lambda: float(INITIAL_ELO))
        matches_played: dict[int, int] = defaultdict(int)

        # Per-team history: {canonical_team_id → list of elo snapshots}
        team_history: dict[int, list] = defaultdict(list)
        team_names: dict[int, str] = {}

        # Per-match Elo snapshots (for training feature lookup)
        # {match_id → {home_elo_before, away_elo_before, home_elo_after, away_elo_after}}
        match_elo_snapshots: dict[int, dict] = {}

        for m in all_matches:
            h_id = canonical_id(m.home_team_id)
            a_id = canonical_id(m.away_team_id)

            # Snapshot ELO BEFORE this match (what the training feature should see)
            h_elo_before = elo[h_id]
            a_elo_before = elo[a_id]

            # Record names (last seen wins)
            if m.home_team:
                team_names[h_id] = m.home_team.name
            if m.away_team:
                team_names[a_id] = m.away_team.name

            # Compute expected and actual scores
            e_home = expected_score(h_elo_before, a_elo_before)
            e_away = 1.0 - e_home

            if m.home_score > m.away_score:
                s_home, s_away = 1.0, 0.0
            elif m.home_score == m.away_score:
                s_home, s_away = 0.5, 0.5
            else:
                s_home, s_away = 0.0, 1.0

            k_h = k_factor(matches_played[h_id])
            k_a = k_factor(matches_played[a_id])

            h_elo_after = h_elo_before + k_h * (s_home - e_home)
            a_elo_after = a_elo_before + k_a * (s_away - e_away)

            # Update state
            elo[h_id] = h_elo_after
            elo[a_id] = a_elo_after
            matches_played[h_id] += 1
            matches_played[a_id] += 1

            # Store per-match snapshot
            match_elo_snapshots[m.id] = {
                "home_team_id": h_id,
                "away_team_id": a_id,
                "home_elo_before": round(h_elo_before, 2),
                "away_elo_before": round(a_elo_before, 2),
                "home_elo_after": round(h_elo_after, 2),
                "away_elo_after": round(a_elo_after, 2),
                "date": m.utc_date.isoformat() if m.utc_date else None,
            }

        logger.info(f"Computed Elo for {len(elo)} unique canonical team IDs")

        # Build output structure
        output = {
            "computed_at": datetime.utcnow().isoformat(),
            "total_matches_processed": len(all_matches),
            "total_teams": len(elo),
            "team_final_elo": {
                str(tid): {
                    "name": team_names.get(tid, f"team_{tid}"),
                    "final_elo": round(elo[tid], 2),
                    "matches_played": matches_played[tid],
                }
                for tid in elo
            },
            "match_elo_snapshots": {
                str(mid): snap for mid, snap in match_elo_snapshots.items()
            },
        }

        OUTPUT_PATH.write_text(json.dumps(output, indent=2))
        logger.info(f"Club Elo data saved to {OUTPUT_PATH}")

        # Print summary of top/bottom clubs
        sorted_teams = sorted(
            output["team_final_elo"].items(),
            key=lambda x: x[1]["final_elo"],
            reverse=True,
        )
        logger.info("\nTop 20 clubs by Elo:")
        for tid, data in sorted_teams[:20]:
            logger.info(f"  {data['name']:40s}  Elo={data['final_elo']:.0f}  ({data['matches_played']} matches)")

        logger.info("\nBottom 10 clubs by Elo:")
        for tid, data in sorted_teams[-10:]:
            logger.info(f"  {data['name']:40s}  Elo={data['final_elo']:.0f}  ({data['matches_played']} matches)")

        return output

    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting club historical Elo computation...")
    result = compute_club_elo()
    print(f"\nDone. Elo for {result['total_teams']} teams computed from {result['total_matches_processed']} matches.")
    print(f"Saved to: {OUTPUT_PATH}")

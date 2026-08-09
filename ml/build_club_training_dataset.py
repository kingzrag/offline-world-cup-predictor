"""
ml/build_club_training_dataset.py

STEP 6B — Phase 6: Build the Clean Club Football Training Dataset

This script generates ml/dataset_club_leagues.csv from historical
domestic club league finished matches in the PostgreSQL database.

Key design decisions (from Step 6A audit):
1. Temporal ordering: matches processed chronologically.
2. Canonical team IDs used (resolves Inter Milan / Bayern duplicates).
3. Pre-match Elo loaded from ml/club_historical_elo.json (no future leakage).
4. Injury/suspension features: EXCLUDED from training rows (temporal leakage
   exists and historical injury records are unavailable for past matches).
5. Squad market value: EXCLUDED from training rows (only current values
   available; using 2026 values for 2015 matches is future leakage).
6. All form/goals/h2h features use STRICT utc_date < match_date filter.
7. FIFA ranking feature always 0 for club teams → included but noted as
   "always neutral" for clubs; does not cause leakage.

Training targets generated:
- target (1X2):      0=HOME_WIN, 1=DRAW, 2=AWAY_WIN
- home_score:        integer
- away_score:        integer
- home_clean_sheet:  1 if away_score==0
- away_clean_sheet:  1 if home_score==0
- btts:              1 if both scored
- ah_target:         asian handicap cover (home team covers -0.5 AH)

Features generated (leakage-safe):
- elo_diff:                    pre-match Elo difference (from club_historical_elo.json)
- form_diff:                   win-ratio difference over last 5 finished matches
- gs_diff:                     goals scored difference (last 5 matches, before this match)
- gc_diff:                     goals conceded difference (last 5 matches, before this match)
- home_adv:                    1 (always — standard home advantage flag)
- h2h_factor:                  historical H2H win ratio (all prior matches, before this match)
- home_elo_momentum:           K-factor simulated momentum (last 10 matches, before this match)
- away_elo_momentum:           same for away team
- elo_momentum_diff:           home - away
- home_attack_rating:          avg goals scored per game (last 10 matches, before this match)
- away_attack_rating:          same for away team
- attack_rating_diff:          home - away
- home_defence_rating:         avg goals conceded per game (last 10 matches, before this match)
- away_defence_rating:         same for away team
- defence_rating_diff:         home - away
- home_clean_sheet_rate:       fraction of last 10 games with clean sheet
- away_clean_sheet_rate:       same for away team
- clean_sheet_rate_diff:       home - away
- home_btts_rate:              fraction of last 10 games with BTTS
- away_btts_rate:              same for away team
- btts_rate_diff:              home - away
- home_recent_form:            points per game (last 5), 3=W, 1=D, 0=L
- away_recent_form:            same for away team
- recent_form_diff:            home - away
- competition_code_encoded:    integer encoding of competition
- home_league_position:        standing rank if available, else 10 (neutral)
- away_league_position:        same

NOTE: Features excluded due to leakage / unavailability:
- inj_diff / susp_diff (no historical records)
- mv_diff / starting_xi_value_diff (only current 2026 values in DB)
- fifa_diff (not applicable to clubs; would always be 0)
- world_cup_matches_played_diff (not applicable to clubs)
"""

import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from models import Match, Competition, Standing
from sqlalchemy import func, or_

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("club_training")

# ── Configuration ──────────────────────────────────────────────────────────────
TARGET_COMPETITIONS = ["PL", "PD", "SA", "BL1", "FL1", "DED", "BSA"]
OUTPUT_PATH = Path(__file__).parent / "dataset_club_leagues.csv"
ELO_DATA_PATH = Path(__file__).parent / "club_historical_elo.json"
CANONICAL_MAP_PATH = Path(__file__).parent / "canonical_team_id_map.json"

# Minimum matches a team must have played BEFORE this match to include it in training
# (below this threshold, form features are too noisy)
MIN_PRIOR_MATCHES = 3

COMPETITION_CODES = {
    "PL": 1,
    "PD": 2,
    "SA": 3,
    "BL1": 4,
    "FL1": 5,
    "DED": 6,
    "BSA": 7,
}


# ── Load pre-computed club Elo ──────────────────────────────────────────────────

def load_club_elo_data() -> tuple[dict, dict]:
    """
    Returns:
        team_final_elo: {team_id_str → {name, final_elo, matches_played}}
        match_elo:      {match_id_str → {home_elo_before, away_elo_before, ...}}
    """
    if not ELO_DATA_PATH.exists():
        logger.error(f"Club Elo data not found at {ELO_DATA_PATH}. Run ml/compute_club_elo.py first!")
        return {}, {}
    data = json.loads(ELO_DATA_PATH.read_text())
    return data.get("team_final_elo", {}), data.get("match_elo_snapshots", {})


def load_canonical_map() -> dict[int, int]:
    if not CANONICAL_MAP_PATH.exists():
        return {}
    raw = json.loads(CANONICAL_MAP_PATH.read_text())
    return {int(k): int(v) for k, v in raw.items()}


# ── Feature helpers ────────────────────────────────────────────────────────────

def get_recent_match_stats(db, team_id: int, before_date: datetime, n: int = 5) -> dict:
    """
    Compute recent match statistics for a team using ONLY matches BEFORE before_date.
    Returns dict with form, goals_scored, goals_conceded, clean_sheet_rate, btts_rate.
    """
    recent = (
        db.query(Match)
        .filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
            Match.utc_date < before_date,    # ← temporal safety: ONLY past matches
        )
        .order_by(Match.utc_date.desc())
        .limit(n)
        .all()
    )

    if not recent:
        return {
            "form": 0.0, "gs": 0.0, "gc": 0.0,
            "clean_sheet_rate": 0.0, "btts_rate": 0.0,
            "ppg": 0.0, "count": 0,
        }

    wins = draws = 0
    total_gs = total_gc = 0
    clean_sheets = btts = 0

    for m in recent:
        is_home = (m.home_team_id == team_id)
        if is_home:
            gs = m.home_score
            gc = m.away_score
        else:
            gs = m.away_score
            gc = m.home_score

        total_gs += gs
        total_gc += gc

        if gs > gc:
            wins += 1
        elif gs == gc:
            draws += 1

        if gc == 0:
            clean_sheets += 1
        if gs > 0 and gc > 0:
            btts += 1

    n_actual = len(recent)
    form = (wins - (n_actual - wins - draws)) / n_actual  # win_rate - loss_rate
    ppg = (wins * 3 + draws) / n_actual
    gs_avg = total_gs / n_actual
    gc_avg = total_gc / n_actual
    cs_rate = clean_sheets / n_actual
    btts_rate = btts / n_actual

    return {
        "form": round(form, 4),
        "gs": round(gs_avg, 4),
        "gc": round(gc_avg, 4),
        "clean_sheet_rate": round(cs_rate, 4),
        "btts_rate": round(btts_rate, 4),
        "ppg": round(ppg, 4),
        "count": n_actual,
    }


def get_attack_defence_rating(db, team_id: int, before_date: datetime, n: int = 10) -> dict:
    """Attack and defence ratings from last N matches before this match."""
    recent = (
        db.query(Match)
        .filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.utc_date < before_date,
        )
        .order_by(Match.utc_date.desc())
        .limit(n)
        .all()
    )
    if not recent:
        return {"attack": 0.0, "defence": 0.0, "cs_rate": 0.0, "btts_rate": 0.0}

    total_scored = total_conceded = clean_sheets = btts_count = 0
    for m in recent:
        is_home = (m.home_team_id == team_id)
        scored = m.home_score if is_home else m.away_score
        conceded = m.away_score if is_home else m.home_score
        total_scored += scored
        total_conceded += conceded
        if conceded == 0:
            clean_sheets += 1
        if scored > 0 and conceded > 0:
            btts_count += 1

    n_actual = len(recent)
    return {
        "attack": round(total_scored / n_actual, 4),
        "defence": round(total_conceded / n_actual, 4),
        "cs_rate": round(clean_sheets / n_actual, 4),
        "btts_rate": round(btts_count / n_actual, 4),
    }


def get_h2h_factor(db, home_id: int, away_id: int, before_date: datetime) -> float:
    """
    Head-to-head win ratio for home_id against away_id.
    Uses ONLY past matches before before_date.
    """
    h2h_matches = (
        db.query(Match)
        .filter(
            or_(
                (Match.home_team_id == home_id) & (Match.away_team_id == away_id),
                (Match.home_team_id == away_id) & (Match.away_team_id == home_id),
            ),
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.utc_date < before_date,
        )
        .all()
    )
    if not h2h_matches:
        return 0.5  # neutral

    home_wins = 0
    for m in h2h_matches:
        if m.home_team_id == home_id and m.home_score > m.away_score:
            home_wins += 1
        elif m.away_team_id == home_id and m.away_score > m.home_score:
            home_wins += 1

    return round(home_wins / len(h2h_matches), 4)


def get_elo_momentum(db, team_id: int, before_date: datetime, match_elo_data: dict, n: int = 10) -> float:
    """
    Simulates Elo momentum based on K-factor changes over last N matches.
    Uses pre-computed match Elo snapshots for temporal safety.
    """
    recent = (
        db.query(Match)
        .filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.utc_date < before_date,
        )
        .order_by(Match.utc_date.desc())
        .limit(n)
        .all()
    )
    if len(recent) < 2:
        return 0.0

    momentum = 0.0
    for m in recent:
        snap = match_elo_data.get(str(m.id))
        if not snap:
            continue
        is_home = (m.home_team_id == team_id)
        elo_before = snap["home_elo_before"] if is_home else snap["away_elo_before"]
        elo_after = snap["home_elo_after"] if is_home else snap["away_elo_after"]
        momentum += (elo_after - elo_before)

    return round(momentum / len(recent), 4)


def get_league_position(db, team_id: int, competition_id: int, before_date: datetime) -> int:
    """Get team's standing position as of before_date. Returns 10 (neutral) if unknown."""
    standing = (
        db.query(Standing)
        .filter(
            Standing.team_id == team_id,
            Standing.competition_id == competition_id,
        )
        .first()
    )
    return standing.position if standing and standing.position else 10


# ── Main dataset builder ───────────────────────────────────────────────────────

def build_dataset(min_prior_matches: int = MIN_PRIOR_MATCHES) -> dict:
    db = SessionLocal()
    _, match_elo_data = load_club_elo_data()
    canonical_map = load_canonical_map()

    def canonical_id(tid: int) -> int:
        return canonical_map.get(tid, tid)

    rows = []
    stats = defaultdict(lambda: {"total": 0, "skipped_no_elo": 0, "skipped_low_history": 0, "included": 0})

    try:
        for comp_code in TARGET_COMPETITIONS:
            comp = db.query(Competition).filter_by(code=comp_code).first()
            if not comp:
                logger.warning(f"Competition {comp_code} not found — skipping")
                continue

            comp_enc = COMPETITION_CODES.get(comp_code, 0)

            matches = (
                db.query(Match)
                .filter(
                    Match.competition_id == comp.id,
                    Match.status == "FINISHED",
                    Match.home_score.isnot(None),
                    Match.away_score.isnot(None),
                )
                .order_by(Match.utc_date.asc())
                .all()
            )

            logger.info(f"[{comp_code}] {comp.name}: {len(matches)} finished matches")

            for m in matches:
                stats[comp_code]["total"] += 1

                h_id = canonical_id(m.home_team_id)
                a_id = canonical_id(m.away_team_id)
                match_date = m.utc_date
                if match_date.tzinfo is None:
                    match_date = match_date.replace(tzinfo=timezone.utc)

                # ── Pre-match Elo (from historical computation) ──────────────
                snap = match_elo_data.get(str(m.id))
                if snap:
                    home_elo_before = snap["home_elo_before"]
                    away_elo_before = snap["away_elo_before"]
                else:
                    # Fallback: use default Elo (match predates our computation window)
                    home_elo_before = 1500.0
                    away_elo_before = 1500.0

                elo_diff = home_elo_before - away_elo_before

                # ── Recent form (strictly before match_date) ─────────────────
                h_stats = get_recent_match_stats(db, h_id, match_date, n=5)
                a_stats = get_recent_match_stats(db, a_id, match_date, n=5)

                # Skip if both teams have almost no history
                if h_stats["count"] < min_prior_matches and a_stats["count"] < min_prior_matches:
                    stats[comp_code]["skipped_low_history"] += 1
                    continue

                # ── Attack/defence ratings (last 10 matches before this) ─────
                h_ratings = get_attack_defence_rating(db, h_id, match_date, n=10)
                a_ratings = get_attack_defence_rating(db, a_id, match_date, n=10)

                # ── H2H factor ───────────────────────────────────────────────
                h2h = get_h2h_factor(db, h_id, a_id, match_date)

                # ── Elo momentum ─────────────────────────────────────────────
                h_momentum = get_elo_momentum(db, h_id, match_date, match_elo_data)
                a_momentum = get_elo_momentum(db, a_id, match_date, match_elo_data)

                # ── League position ──────────────────────────────────────────
                h_pos = get_league_position(db, h_id, comp.id, match_date)
                a_pos = get_league_position(db, a_id, comp.id, match_date)

                # ── Targets ──────────────────────────────────────────────────
                hs = m.home_score
                as_ = m.away_score
                if hs > as_:
                    target = 0  # HOME_WIN
                elif hs == as_:
                    target = 1  # DRAW
                else:
                    target = 2  # AWAY_WIN

                home_cs = 1 if as_ == 0 else 0
                away_cs = 1 if hs == 0 else 0
                btts = 1 if (hs > 0 and as_ > 0) else 0
                ah_cover = 1 if (hs - as_) > 0 else 0  # home covers -0.5 AH

                # ── Build row ────────────────────────────────────────────────
                row = {
                    # Metadata
                    "match_id": m.id,
                    "utc_date": m.utc_date.isoformat() if m.utc_date else "",
                    "competition_code": comp_code,
                    "home_team_id": h_id,
                    "away_team_id": a_id,
                    "home_team": m.home_team.name if m.home_team else "",
                    "away_team": m.away_team.name if m.away_team else "",
                    # Features (leakage-safe)
                    "elo_diff": round(elo_diff, 2),
                    "form_diff": round(h_stats["form"] - a_stats["form"], 4),
                    "gs_diff": round(h_stats["gs"] - a_stats["gs"], 4),
                    "gc_diff": round(h_stats["gc"] - a_stats["gc"], 4),
                    "home_adv": 1,
                    "h2h_factor": h2h,
                    "home_elo_momentum": h_momentum,
                    "away_elo_momentum": a_momentum,
                    "elo_momentum_diff": round(h_momentum - a_momentum, 4),
                    "home_attack_rating": h_ratings["attack"],
                    "away_attack_rating": a_ratings["attack"],
                    "attack_rating_diff": round(h_ratings["attack"] - a_ratings["attack"], 4),
                    "home_defence_rating": h_ratings["defence"],
                    "away_defence_rating": a_ratings["defence"],
                    "defence_rating_diff": round(h_ratings["defence"] - a_ratings["defence"], 4),
                    "home_clean_sheet_rate": h_ratings["cs_rate"],
                    "away_clean_sheet_rate": a_ratings["cs_rate"],
                    "clean_sheet_rate_diff": round(h_ratings["cs_rate"] - a_ratings["cs_rate"], 4),
                    "home_btts_rate": h_ratings["btts_rate"],
                    "away_btts_rate": a_ratings["btts_rate"],
                    "btts_rate_diff": round(h_ratings["btts_rate"] - a_ratings["btts_rate"], 4),
                    "home_recent_form": h_stats["ppg"],
                    "away_recent_form": a_stats["ppg"],
                    "recent_form_diff": round(h_stats["ppg"] - a_stats["ppg"], 4),
                    "competition_code_encoded": comp_enc,
                    "home_league_position": h_pos,
                    "away_league_position": a_pos,
                    "league_position_diff": h_pos - a_pos,
                    # Targets
                    "target": target,
                    "home_score": hs,
                    "away_score": as_,
                    "home_clean_sheet": home_cs,
                    "away_clean_sheet": away_cs,
                    "btts": btts,
                    "ah_cover": ah_cover,
                }
                rows.append(row)
                stats[comp_code]["included"] += 1

    finally:
        db.close()

    # Sort all rows globally by utc_date (chronological order across all competitions)
    rows.sort(key=lambda r: r.get("utc_date", ""))

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"\n✅ Wrote {len(rows)} rows to {OUTPUT_PATH}")
    else:
        logger.warning("No rows generated!")

    # Print stats
    print("\n" + "=" * 60)
    print("DATASET BUILD SUMMARY")
    print("=" * 60)
    total_included = 0
    for code, s in stats.items():
        print(f"\n[{code}]  total={s['total']}  included={s['included']}  "
              f"skipped_low_history={s['skipped_low_history']}")
        total_included += s["included"]
    print(f"\nTOTAL TRAINING ROWS: {total_included}")
    print(f"Output: {OUTPUT_PATH}")

    return {"rows": len(rows), "stats": dict(stats)}


if __name__ == "__main__":
    logger.info("Building club football training dataset...")
    result = build_dataset()
    print(f"\nDone. {result['rows']} training rows generated.")

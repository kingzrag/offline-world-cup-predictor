"""
ml/download_historical_club_data.py

STEP 6B — Phase 1: Download and ingest historical club football data.

Source: football-data.co.uk (free, CC-BY license)
- Premier League (PL)    → div code E0
- La Liga (PD)           → div code SP1
- Serie A (SA)           → div code I1
- Bundesliga (BL1)       → div code D1
- Ligue 1 (FL1)          → div code F1
- Eredivisie (DED)       → div code N1

Seasons: 2015-16 through 2024-25 (10 seasons)

NOTE:
- BSA (Brasileirão) is NOT available on football-data.co.uk.
  The 2026 season data already in DB will be used as-is.
- Does NOT drop existing matches.
- Uses a deterministic duplicate key:
    (competition_id, utc_date::date, home_team_id, away_team_id)
- Creates new Team records if a team is not found in DB.
- Marks all imported matches as 'FINISHED' with source='FDCO_IMPORT'.
"""

import logging
import sys
import io
import os
import datetime
from pathlib import Path
from typing import Optional

import requests
import pandas as pd

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from models import Match, Team, Competition

from ml.team_name_mappings import (
    FDCO_LEAGUE_MAP,
    TARGET_SEASONS,
    SEASON_LABELS,
    normalize_team_name,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("fdco_ingest")

# ── constants ──────────────────────────────────────────────────────────────────
FDCO_SOURCE_TAG = "FDCO_IMPORT"
REQUEST_TIMEOUT = 20   # seconds per CSV download

# ── helpers ────────────────────────────────────────────────────────────────────

def fetch_csv(url: str) -> Optional[pd.DataFrame]:
    """Download a football-data.co.uk CSV and return as DataFrame. Returns None on failure."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        # Keep only rows with valid FTHG/FTAG (full-time home/away goals)
        df = df.dropna(subset=["FTHG", "FTAG", "Date", "HomeTeam", "AwayTeam"])
        df["FTHG"] = df["FTHG"].astype(int)
        df["FTAG"] = df["FTAG"].astype(int)
        return df
    except Exception as e:
        logger.warning(f"  Failed to fetch {url}: {e}")
        return None


def parse_date(date_str: str) -> Optional[datetime.datetime]:
    """Parse football-data date string (DD/MM/YY or DD/MM/YYYY) into UTC datetime."""
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            d = datetime.datetime.strptime(date_str.strip(), fmt)
            return d.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    return None


def get_or_create_team(db, canonical_name: str) -> Optional[Team]:
    """Get team by canonical name, or create a minimal shell record if not found."""
    team = db.query(Team).filter(Team.name == canonical_name).first()
    if team:
        return team
    # Try partial match (e.g. "Arsenal FC" for "Arsenal")
    clean = canonical_name.lower().replace(" fc", "").replace(" cf", "").strip()
    team = db.query(Team).filter(Team.name.ilike(f"%{clean}%")).first()
    if team:
        return team
    # Create a minimal shell team record
    logger.info(f"    Creating new Team record: '{canonical_name}'")
    team = Team(
        name=canonical_name,
        short_name=canonical_name[:20],
        tla=canonical_name[:3].upper(),
    )
    db.add(team)
    db.flush()   # get the ID without committing yet
    return team


def match_already_exists(db, competition_id: int, match_date: datetime.datetime,
                          home_team_id: int, away_team_id: int) -> bool:
    """Check if a match with the same (competition, date, home_team, away_team) already exists."""
    date_only = match_date.date()
    existing = db.query(Match).filter(
        Match.competition_id == competition_id,
        Match.home_team_id == home_team_id,
        Match.away_team_id == away_team_id,
        # Match on the same calendar date (ignore time)
        Match.utc_date >= datetime.datetime(date_only.year, date_only.month, date_only.day, tzinfo=datetime.timezone.utc),
        Match.utc_date < datetime.datetime(date_only.year, date_only.month, date_only.day, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=1),
    ).first()
    return existing is not None


# ── main ingestion ─────────────────────────────────────────────────────────────

def ingest_all(dry_run: bool = False) -> dict:
    """
    Download and ingest historical club football data.
    Returns a summary dict with counts per competition per season.
    """
    db = SessionLocal()
    summary = {}
    total_inserted = 0
    total_skipped_dup = 0
    total_skipped_team = 0

    try:
        for comp_code, league_cfg in FDCO_LEAGUE_MAP.items():
            div = league_cfg["div"]
            url_pattern = league_cfg["url_pattern"]
            comp_obj = db.query(Competition).filter_by(code=comp_code).first()
            if not comp_obj:
                logger.error(f"Competition {comp_code} not found in DB — skipping")
                continue

            summary[comp_code] = {"competition": comp_obj.name, "seasons": {}, "total_inserted": 0}
            logger.info(f"\n{'='*60}")
            logger.info(f"[{comp_code}] {comp_obj.name} (div={div})")
            logger.info(f"{'='*60}")

            for season_code in TARGET_SEASONS:
                season_label = SEASON_LABELS[season_code]
                url = url_pattern.format(season=season_code, div=div)
                logger.info(f"  Season {season_label} → {url}")

                df = fetch_csv(url)
                if df is None or len(df) == 0:
                    logger.warning(f"  → No data for {comp_code} {season_label}")
                    summary[comp_code]["seasons"][season_label] = {"fetched": 0, "inserted": 0, "dup": 0, "err": 0}
                    continue

                logger.info(f"  → Fetched {len(df)} rows")
                inserted = 0
                dup = 0
                err = 0

                for _, row in df.iterrows():
                    raw_home = str(row["HomeTeam"]).strip()
                    raw_away = str(row["AwayTeam"]).strip()
                    canonical_home = normalize_team_name(raw_home)
                    canonical_away = normalize_team_name(raw_away)

                    # Parse date
                    match_date = parse_date(str(row["Date"]))
                    if match_date is None:
                        logger.debug(f"    Bad date '{row['Date']}' — skipping")
                        err += 1
                        continue

                    home_goals = int(row["FTHG"])
                    away_goals = int(row["FTAG"])

                    # Resolve teams
                    home_team = get_or_create_team(db, canonical_home)
                    away_team = get_or_create_team(db, canonical_away)

                    if not home_team or not away_team:
                        logger.warning(f"    Cannot resolve teams: {raw_home} | {raw_away}")
                        total_skipped_team += 1
                        err += 1
                        continue

                    # Check for duplicate
                    if match_already_exists(db, comp_obj.id, match_date, home_team.id, away_team.id):
                        dup += 1
                        total_skipped_dup += 1
                        continue

                    # Determine 1X2 winner
                    if home_goals > away_goals:
                        winner = "HOME_TEAM"
                    elif away_goals > home_goals:
                        winner = "AWAY_TEAM"
                    else:
                        winner = "DRAW"

                    if not dry_run:
                        match = Match(
                            competition_id=comp_obj.id,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            utc_date=match_date,
                            status="FINISHED",
                            home_score=home_goals,
                            away_score=away_goals,
                            winner=winner,
                            stage=f"FDCO_{season_label}",
                            # api_id left NULL (source is FDCO)
                        )
                        db.add(match)
                        inserted += 1
                        total_inserted += 1

                if not dry_run:
                    db.commit()

                summary[comp_code]["seasons"][season_label] = {
                    "fetched": len(df),
                    "inserted": inserted,
                    "dup": dup,
                    "err": err,
                }
                summary[comp_code]["total_inserted"] += inserted
                logger.info(f"  → Inserted {inserted}, Dup {dup}, Err {err}")

    except Exception as e:
        db.rollback()
        logger.error(f"FATAL: {e}", exc_info=True)
    finally:
        db.close()

    logger.info(f"\n\nTOTAL INSERTED: {total_inserted}")
    logger.info(f"TOTAL SKIPPED (duplicates): {total_skipped_dup}")
    logger.info(f"TOTAL SKIPPED (team not resolved): {total_skipped_team}")

    return summary


def print_summary(summary: dict) -> None:
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    grand_total = 0
    for comp_code, data in summary.items():
        print(f"\n[{comp_code}] {data['competition']}")
        for season, counts in data["seasons"].items():
            status = "✅" if counts["inserted"] > 0 else ("⏭" if counts["dup"] > 0 else "❌")
            print(f"  {status} {season}: fetched={counts['fetched']} inserted={counts['inserted']} dup={counts['dup']} err={counts['err']}")
        print(f"  TOTAL INSERTED: {data['total_inserted']}")
        grand_total += data["total_inserted"]
    print(f"\nGRAND TOTAL NEW MATCHES INSERTED: {grand_total}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest historical club football data from football-data.co.uk")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to DB")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE — no DB writes will be made")
    else:
        logger.info("LIVE MODE — data will be written to DB")

    summary = ingest_all(dry_run=args.dry_run)
    print_summary(summary)

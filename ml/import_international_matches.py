import os
import sys
import hashlib
import pandas as pd
from pathlib import Path
from sqlalchemy import insert, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Ensure project root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from database.connection import SessionLocal
from models import Match, Competition, Team
from utils.logger import logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATA_DIR = ROOT / "data" / "international"
CSV_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
CSV_PATH = DATA_DIR / "results.csv"
COVERAGE_START_YEAR = 2000
COVERAGE_END_YEAR = 2026
CHUNK_SIZE = 5000

# Mapping of tournament names to our internal competition codes (must match entries in `competitions` table)
TOURNAMENT_CODE_MAP = {
    "FIFA World Cup": "WC",
    "FIFA World Cup qualification": "WCQ",
    "World Cup Qualifiers": "WCQ",
    "UEFA Nations League": "UNL",
    "UEFA Euro": "EU",
    "UEFA Euro qualification": "EUQ",
    "Copa America": "CA",
    "African Cup of Nations": "AFCON",
    "African Cup of Nations qualification": "AFCONQ",
    "AFC Asian Cup": "ASIAN",
    "AFC Asian Cup qualification": "ASIANQ",
    "CONCACAF Nations League": "CNL",
    "International friendly": "FRI",
    "Friendly": "FRI",
}

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def download_csv():
    """Download the CSV file if it does not already exist."""
    if not DATA_DIR.exists():
        logger.info(f"Creating data directory at {DATA_DIR}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.is_file():
        logger.info(f"CSV already present at {CSV_PATH}")
        return
    import subprocess, shlex
    logger.info(f"Downloading CSV from {CSV_URL}")
    cmd = f"curl -L {shlex.quote(str(CSV_URL))} -o {shlex.quote(str(CSV_PATH))}"
    subprocess.run(cmd, shell=True, check=True)
    logger.info("Download complete")

def generate_external_id(row: pd.Series) -> str:
    """Create a deterministic external match ID.
    Preference: use existing `match_id` column if present; otherwise hash composite key.
    """
    if "match_id" in row and pd.notna(row["match_id"]):
        return str(row["match_id"]).strip()
    # Composite key: date|home|away|tournament
    key = f"{row['date']}|{row['home_team']}|{row['away_team']}|{row['tournament']}"
    # Return truncated SHA256 hash to fit varchar(50)
    return hashlib.sha256(key.encode()).hexdigest()[:50]


def get_or_create_competition(session, name: str) -> Competition:
    """Return an existing Competition object or create a new one if missing."""
    comp = session.execute(select(Competition).where(Competition.name == name)).scalar_one_or_none()
    if comp:
        return comp
    code = TOURNAMENT_CODE_MAP.get(name, name[:3].upper())
    comp = Competition(name=name, code=code)
    session.add(comp)
    session.flush()  # assign id
    return comp

def get_or_create_team(session, name: str) -> Team:
    """Return an existing Team object or create it if missing."""
    team = session.execute(select(Team).where(Team.name == name)).scalar_one_or_none()
    if team:
        return team
    team = Team(name=name)
    session.add(team)
    session.flush()
    return team

def insert_matches(df: pd.DataFrame, session) -> dict:
    """Insert matches from a DataFrame chunk.
    Returns a dict with statistics.
    """
    stats = {
        "processed": 0,
        "inserted": 0,
        "duplicates": 0,
        "missing_scores": 0,
        "schema_mismatch": 0,
        "missing_competitions": 0,
        "missing_teams": 0,
        "skipped": 0,
    }
    for _, row in df.iterrows():
        stats["processed"] += 1
        external_id = generate_external_id(row)
        # Check for duplicate via api_id (Match.api_id field)
        existing = session.execute(select(Match).where(Match.api_id == external_id)).scalar_one_or_none()
        if existing:
            stats["duplicates"] += 1
            continue
        # Competition
        # Competition lookup with missing logging
        comp = session.execute(select(Competition).where(Competition.name == row["tournament"]))
        comp = comp.scalar_one_or_none()
        if not comp:
            stats["missing_competitions"] += 1
            comp = get_or_create_competition(session, row["tournament"])
        else:
            # Ensure we have a persistent object
            pass
        # Teams
        # Home team lookup with missing logging
        home = session.execute(select(Team).where(Team.name == row["home_team"]))
        home = home.scalar_one_or_none()
        if not home:
            stats["missing_teams"] += 1
            home = get_or_create_team(session, row["home_team"])
        else:
            pass
        # Away team lookup with missing logging
        away = session.execute(select(Team).where(Team.name == row["away_team"]))
        away = away.scalar_one_or_none()
        if not away:
            stats["missing_teams"] += 1
            away = get_or_create_team(session, row["away_team"])
        else:
            pass
        # Build Match object
        try:
            # Ensure required score fields are present and numeric
            home_score_raw = row["home_score"] if "home_score" in row else None
            away_score_raw = row["away_score"] if "away_score" in row else None
            try:
                # Safely convert scores; skip if any missing
                if pd.isna(home_score_raw) or pd.isna(away_score_raw):
                    logger.warning(f"Skipping match {external_id} due to missing score(s)")
                    stats["missing_scores"] += 1
                    stats["skipped"] += 1
                    continue
                home_score = int(home_score_raw)
                away_score = int(away_score_raw)
            except Exception as e:
                logger.warning(f"Skipping match {external_id} due to invalid score values: {e}")
                stats["missing_scores"] += 1
                continue
            # If either score missing, we cannot determine winner – still insert but set winner to None
            winner = None
            if home_score is not None and away_score is not None:
                if home_score > away_score:
                    winner = "HOME_TEAM"
                elif away_score > home_score:
                    winner = "AWAY_TEAM"
                else:
                    winner = "DRAW"
            # Build Match with only valid columns
            match_data = {
                "api_id": external_id,
                "competition_id": comp.id,
                "home_team_id": home.id,
                "away_team_id": away.id,
                "utc_date": pd.to_datetime(row["date"], errors="coerce"),
                "status": "FINISHED",
                "home_score": home_score,
                "away_score": away_score,
                "winner": winner,
                "stage": None,
                "group": None,
            }
            # Print match fields for first successful row
            if stats["processed"] == 1:
                logger.info(f"First match fields: {match_data}")
            match = Match(**match_data)

            session.add(match)
            stats["inserted"] += 1
        except Exception as e:
            logger.warning(f"Failed to create match from row {external_id}: {e}")
            stats["schema_mismatch"] += 1
    return stats

def rebuild_world_cup_dataset():
    """Run the existing world‑cup dataset builder after import."""
    try:
        import importlib
        mod = importlib.import_module("ml.build_dataset_world_cup")
        if hasattr(mod, "build_dataset"):
            logger.info("Rebuilding dataset_world_cup.csv …")
            mod.build_dataset()
            logger.info("World‑cup dataset rebuild complete")
        else:
            logger.error("build_dataset function not found in ml.build_dataset_world_cup")
    except Exception as e:
        logger.error(f"Error rebuilding world‑cup dataset: {e}")

def generate_coverage_report(session) -> pd.DataFrame:
    """Create a DataFrame with matches by competition and year, plus team count.
    Also returns total rows and duplicate rows (derived from import stats)."""
    # Matches per competition
    comp_counts = (
        session.query(Competition.name, func.count(Match.id))
        .join(Match, Match.competition_id == Competition.id)
        .filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01", Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31")
        .group_by(Competition.name)
        .order_by(func.count(Match.id).desc())
        .all()
    )
    # Matches per year
    year_counts = (
        session.query(func.extract('year', Match.utc_date).label('year'), func.count(Match.id))
        .filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01", Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31")
        .group_by('year')
        .order_by('year')
        .all()
    )
    # Distinct national teams (home + away)
    home_teams = session.query(Match.home_team_id).filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01", Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31")
    away_teams = session.query(Match.away_team_id).filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01", Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31")
    team_ids = set([tid for (tid,) in home_teams] + [tid for (tid,) in away_teams])
    team_count = len(team_ids)

    # Build report DataFrame
    report = pd.DataFrame({
        "competition": [c for c, _ in comp_counts],
        "matches": [cnt for _, cnt in comp_counts]
    })
    report_years = pd.DataFrame({
        "year": [int(y) for y, _ in year_counts],
        "matches": [cnt for _, cnt in year_counts]
    })
    summary = {
        "total_matches": sum(cnt for _, cnt in comp_counts),
        "team_count": team_count,
        "matches_by_competition": report,
        "matches_by_year": report_years,
    }
    return summary

def main():
    logger.info("--- International Match Import Pipeline Start ---")
    download_csv()
    logger.info(f"Reading CSV from {CSV_PATH}")
    # Load CSV with only required columns (ignore others)
    df = pd.read_csv(CSV_PATH, parse_dates=["date"], low_memory=False)
    # Filter years and competitions
    mask_year = (df["date"].dt.year >= COVERAGE_START_YEAR) & (df["date"].dt.year <= COVERAGE_END_YEAR)
    target_tournaments = list(TOURNAMENT_CODE_MAP.keys())
    mask_tour = df["tournament"].isin(target_tournaments)
    df = df[mask_year & mask_tour].copy()
    logger.info(f"Filtered to {len(df)} rows (years {COVERAGE_START_YEAR}-{COVERAGE_END_YEAR})")
    session = SessionLocal()
    total_stats = {"processed": 0, "inserted": 0, "duplicates": 0}
    try:
        for start in range(0, len(df), CHUNK_SIZE):
            chunk = df.iloc[start:start + CHUNK_SIZE]
            stats = insert_matches(chunk, session)
            session.commit()
            # Accumulate
            for k in total_stats:
                total_stats[k] += stats[k]
            logger.info(
                f"Chunk {start // CHUNK_SIZE + 1}: processed {stats['processed']}, inserted {stats['inserted']}, duplicates {stats['duplicates']}, "
                f"missing_scores {stats.get('missing_scores',0)}, missing_competitions {stats.get('missing_competitions',0)}, "
                f"missing_teams {stats.get('missing_teams',0)}, skipped {stats.get('skipped',0)}, schema_mismatch {stats.get('schema_mismatch',0)}"
            )
        logger.info("Import completed.")
        logger.info(f"Total processed: {total_stats['processed']}, inserted: {total_stats['inserted']}, duplicates skipped: {total_stats['duplicates']}")
        # Coverage report
        from sqlalchemy import func
        coverage = generate_coverage_report(session)
        # Print human readable report
        logger.info("--- Coverage Report ---")
        logger.info(f"Total imported matches: {coverage['total_matches']}")
        logger.info(f"Distinct national teams: {coverage['team_count']}")
        logger.info("Matches by competition (top 10):")
        logger.info(coverage['matches_by_competition'].head(10).to_string(index=False))
        logger.info("Matches by year (last 5 years):")
        logger.info(coverage['matches_by_year'].tail(5).to_string(index=False))
        # Rebuild world cup dataset
        rebuild_world_cup_dataset()
        # After rebuild, report dataset size and missing values
        dataset_path = Path(__file__).resolve().parents[1] / "ml" / "dataset_world_cup.csv"
        if dataset_path.is_file():
            df_wc = pd.read_csv(dataset_path)
            rows = len(df_wc)
            missing = df_wc.isnull().sum().to_dict()
            logger.info(f"World‑cup dataset rows: {rows}")
            logger.info("Missing values by feature:")
            for col, cnt in missing.items():
                if cnt > 0:
                    logger.info(f"  {col}: {cnt}")
        else:
            logger.warning("World‑cup dataset file not found after rebuild.")
    finally:
        session.close()
    logger.info("--- Pipeline Finished ---")

if __name__ == "__main__":
    main()

import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import func, select

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from database.connection import SessionLocal
from models import Match, Competition, Team
from utils.logger import logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
COVERAGE_START_YEAR = 2000
COVERAGE_END_YEAR = 2026

def generate_report():
    session = SessionLocal()
    try:
        # Total imported rows
        total = session.execute(select(func.count()).select_from(Match)).scalar()
        # Matches by competition (top 15)
        comp_counts = (
            session.query(Competition.name, func.count(Match.id))
            .join(Match, Match.competition_id == Competition.id)
            .filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01",
                   Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31")
            .group_by(Competition.name)
            .order_by(func.count(Match.id).desc())
            .all()
        )
        comp_df = pd.DataFrame(comp_counts, columns=["competition", "matches"])
        # Matches by year
        year_counts = (
            session.query(func.extract('year', Match.utc_date).label('year'), func.count(Match.id))
            .filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01",
                   Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31")
            .group_by('year')
            .order_by('year')
            .all()
        )
        year_df = pd.DataFrame(year_counts, columns=["year", "matches"]).astype({"year": int})
        # Distinct national teams (home + away)
        home_ids = session.query(Match.home_team_id).filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01",
                                                   Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31").all()
        away_ids = session.query(Match.away_team_id).filter(Match.utc_date >= f"{COVERAGE_START_YEAR}-01-01",
                                                   Match.utc_date <= f"{COVERAGE_END_YEAR}-12-31").all()
        team_ids = set([i for (i,) in home_ids] + [i for (i,) in away_ids])
        team_count = len(team_ids)
        # Output report
        logger.info("--- Import Validation Report ---")
        logger.info(f"Total imported matches: {total}")
        logger.info(f"Distinct national teams: {team_count}")
        logger.info("Matches by competition (top 10):")
        logger.info(comp_df.head(10).to_string(index=False))
        logger.info("Matches by year (last 5 years):")
        logger.info(year_df.tail(5).to_string(index=False))
        # Save CSV reports
        out_dir = ROOT / "data" / "international"
        out_dir.mkdir(parents=True, exist_ok=True)
        comp_df.to_csv(out_dir / "validation_matches_by_competition.csv", index=False)
        year_df.to_csv(out_dir / "validation_matches_by_year.csv", index=False)
        logger.info(f"CSV validation reports written to {out_dir}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_report()

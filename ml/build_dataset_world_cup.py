import csv
import os
import sys

# Add root folder to sys.path so we can import from database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, func
from database.connection import SessionLocal
from models import Match, Competition, Team, NationalTeamInjury, NationalTeamSuspension
from ml.features import extract_ml_features
from utils.logger import logger

# ----------------------------------------------------------------------
# International competition names – must match the `name` column in `competitions`
# ----------------------------------------------------------------------
INTERNATIONAL_COMPETITIONS = [
    "FIFA World Cup",
    "FIFA World Cup Qualifiers",
    "UEFA Nations League",
    "UEFA Euro",
    "Copa America",
    "AFCON",
    "AFC Asian Cup",
    "CONCACAF Nations League",
    "International Friendly",
    "International Friendlies",
]


def build_dataset():
    """Build dataset_world_cup.csv using only international matches."""
    db = SessionLocal()
    try:
        logger.info("Building international-only dataset …")

        # Find competition IDs that match our international list
        intl_competitions = (
            db.query(Competition)
            .filter(Competition.name.in_(INTERNATIONAL_COMPETITIONS))
            .all()
        )

        if not intl_competitions:
            logger.warning(
                "No international competitions found in the database. "
                "The dataset will contain 0 rows. "
                "Available competitions:"
            )
            all_comps = db.query(Competition).all()
            for c in all_comps:
                logger.info(f"  - id={c.id} name='{c.name}' code='{c.code}'")

            # Fall back: build with ALL finished matches (same as build_dataset.py)
            logger.info("Falling back to ALL finished matches …")
            matches = (
                db.query(Match)
                .filter_by(status="FINISHED")
                .order_by(Match.utc_date)
                .all()
            )
        else:
            comp_ids = [c.id for c in intl_competitions]
            comp_names = [c.name for c in intl_competitions]
            logger.info(f"Found {len(intl_competitions)} international competitions: {comp_names}")

            matches = (
                db.query(Match)
                .filter(Match.status == "FINISHED", Match.competition_id.in_(comp_ids))
                .order_by(Match.utc_date)
                .all()
            )

        logger.info(f"Retrieved {len(matches)} finished international matches.")

        if not matches:
            logger.error("No finished international matches found. Cannot build dataset.")
            return

        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_world_cup.csv")

        # Build headers from the first match, including team names
        sample = matches[0]
        comp = db.query(Competition).filter_by(id=sample.competition_id).first()
        comp_code = comp.code if comp else "WC"

        sample_features = extract_ml_features(
            db, sample.home_team_id, sample.away_team_id, sample.utc_date, comp_code,
            match_stage=sample.stage
        )
        # Add home and away team names to the CSV columns
        headers = ["home_team", "away_team"] + list(sample_features.keys()) + ["target"]

        rows_written = 0
        with open(dataset_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for idx, m in enumerate(matches):
                if idx % 50 == 0:
                    logger.info(f"Processing match {idx + 1}/{len(matches)} …")

                comp = db.query(Competition).filter_by(id=m.competition_id).first()
                comp_code = comp.code if comp else "WC"

                try:
                    # Log missing info
                    home_team = db.query(Team).filter_by(id=m.home_team_id).first()
                    away_team = db.query(Team).filter_by(id=m.away_team_id).first()
                    
                    if home_team and (home_team.squad_market_value is None or home_team.squad_market_value == 0.0):
                        logger.warning(f"Missing squad market value for team: {home_team.name}")
                    if away_team and (away_team.squad_market_value is None or away_team.squad_market_value == 0.0):
                        logger.warning(f"Missing squad market value for team: {away_team.name}")
                        
                    home_inj_count = db.query(NationalTeamInjury).filter_by(team_id=m.home_team_id).count()
                    away_inj_count = db.query(NationalTeamInjury).filter_by(team_id=m.away_team_id).count()
                    if home_inj_count == 0 and home_team:
                        logger.info(f"Missing injury data (0 active injuries) for team: {home_team.name}")
                    if away_inj_count == 0 and away_team:
                        logger.info(f"Missing injury data (0 active injuries) for team: {away_team.name}")
                        
                    home_susp_count = db.query(NationalTeamSuspension).filter_by(team_id=m.home_team_id).count()
                    away_susp_count = db.query(NationalTeamSuspension).filter_by(team_id=m.away_team_id).count()
                    if home_susp_count == 0 and home_team:
                        logger.info(f"Missing suspension data (0 active suspensions) for team: {home_team.name}")
                    if away_susp_count == 0 and away_team:
                        logger.info(f"Missing suspension data (0 active suspensions) for team: {away_team.name}")

                    features = extract_ml_features(
                        db, m.home_team_id, m.away_team_id, m.utc_date, comp_code,
                        match_stage=m.stage
                    )

                    if m.winner == "HOME_TEAM":
                        target = 2
                    elif m.winner == "DRAW":
                        target = 1
                    elif m.winner == "AWAY_TEAM":
                        target = 0
                    else:
                        logger.warning(f"Match {m.id} has unknown winner '{m.winner}'. Skipping.")
                        continue

                    row = features.copy()
                    # Include team identifiers for downstream analysis
                    row["home_team"] = home_team.name if home_team else ""
                    row["away_team"] = away_team.name if away_team else ""
                    row["target"] = target
                    writer.writerow(row)
                    rows_written += 1
                except Exception as e:
                    logger.warning(f"Failed to extract features for match {m.id}: {e}. Skipping.")
                    continue

        logger.info(f"International dataset complete. Saved {rows_written} rows to {dataset_path}.")

    finally:
        db.close()


if __name__ == "__main__":
    build_dataset()

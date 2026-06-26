import csv
import os
import sys
import random

# Add root folder to sys.path so we can import from database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, func
from database.connection import SessionLocal
from models import Match, Competition, Team, Injury, Suspension, NationalTeamPlayer
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

def add_simulated_injuries(db, team_id):
    """Add simulated realistic injuries to a team's players for training purposes."""
    team = db.query(Team).filter_by(id=team_id).first()
    if not team:
        return
    players = (
        db.query(NationalTeamPlayer)
        .filter_by(team_id=team_id)
        .all()
    )
    if not players:
        return

    # Randomly injure 1-3 players
    num_injuries = random.randint(0, 3)
    injured_players = random.sample(players, min(num_injuries, len(players)))

    for p in injured_players:
        inj = Injury(
            player_name=p.player_name,
            team_id=team_id,
            team_name=team.name,
            injury_type="Simulated Training Injury",
            player_market_value=p.market_value
        )
        db.add(inj)

def build_dataset():
    """Build dataset_goals.csv using only international matches with recorded scores."""
    db = SessionLocal()
    try:
        logger.info("Building goals prediction dataset …")

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

            # Fall back: build with ALL finished matches with non-null scores
            logger.info("Falling back to ALL finished matches …")
            matches = (
                db.query(Match)
                .filter(Match.status == "FINISHED", Match.home_score != None, Match.away_score != None)
                .order_by(Match.utc_date)
                .all()
            )
        else:
            comp_ids = [c.id for c in intl_competitions]
            comp_names = [c.name for c in intl_competitions]
            logger.info(f"Found {len(intl_competitions)} international competitions: {comp_names}")

            matches = (
                db.query(Match)
                .filter(
                    Match.status == "FINISHED",
                    Match.competition_id.in_(comp_ids),
                    Match.home_score != None,
                    Match.away_score != None
                )
                .order_by(Match.utc_date)
                .all()
            )

        logger.info(f"Retrieved {len(matches)} finished international matches with valid scores.")

        if not matches:
            logger.error("No finished international matches found. Cannot build dataset.")
            return

        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_goals.csv")

        # Build headers from the first match, including team names and goal scores
        sample = matches[0]
        comp = db.query(Competition).filter_by(id=sample.competition_id).first()
        comp_code = comp.code if comp else "WC"

        sample_features = extract_ml_features(
            db, sample.home_team_id, sample.away_team_id, sample.utc_date, comp_code,
            match_stage=sample.stage
        )
        # Add home and away team names, plus home_score and away_score targets to the CSV columns
        headers = ["home_team", "away_team"] + list(sample_features.keys()) + ["home_score", "away_score"]

        rows_written = 0
        with open(dataset_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for idx, m in enumerate(matches):
                if idx % 100 == 0:
                    logger.info(f"Processing match {idx + 1}/{len(matches)} …")

                comp = db.query(Competition).filter_by(id=m.competition_id).first()
                comp_code = comp.code if comp else "WC"

                try:
                    home_team = db.query(Team).filter_by(id=m.home_team_id).first()
                    away_team = db.query(Team).filter_by(id=m.away_team_id).first()

                    # --- SIMULATE INJURIES FOR TRAINING ---
                    # Clear any existing injuries/suspensions for this iteration
                    db.query(Injury).filter_by(team_id=m.home_team_id).delete()
                    db.query(Injury).filter_by(team_id=m.away_team_id).delete()
                    db.query(Suspension).filter_by(team_id=m.home_team_id).delete()
                    db.query(Suspension).filter_by(team_id=m.away_team_id).delete()

                    # Add simulated injuries
                    add_simulated_injuries(db, m.home_team_id)
                    add_simulated_injuries(db, m.away_team_id)
                    db.flush()  # So queries see the new injuries
                    # --- END SIMULATE ---

                    features = extract_ml_features(
                        db, m.home_team_id, m.away_team_id, m.utc_date, comp_code,
                        match_stage=m.stage
                    )

                    row = features.copy()
                    # Include team identifiers and targets
                    row["home_team"] = home_team.name if home_team else ""
                    row["away_team"] = away_team.name if away_team else ""
                    row["home_score"] = m.home_score
                    row["away_score"] = m.away_score
                    writer.writerow(row)
                    rows_written += 1
                except Exception as e:
                    logger.warning(f"Failed to extract features for match {m.id}: {e}. Skipping.")
                    continue

        logger.info(f"Goals dataset complete. Saved {rows_written} rows to {dataset_path}.")

    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    build_dataset()

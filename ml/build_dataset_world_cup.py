import csv
import os
import sys
import random
import pandas as pd

# Add root folder to sys.path so we can import from database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, func
from database.connection import SessionLocal
from models import Match, Competition, Team, Injury, Suspension, NationalTeamPlayer
from ml.features import extract_ml_features
from ml.kaggle_features import clear_kaggle_cache
from utils.logger import logger

# Load Kaggle teams for filtering
KAGGLE_TEAMS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   'data', 'temp_download', 'teams.csv')
KAGGLE_TEAM_NAMES = set()

if os.path.exists(KAGGLE_TEAMS_FILE):
    try:
        kaggle_df = pd.read_csv(KAGGLE_TEAMS_FILE)
        KAGGLE_TEAM_NAMES = set(kaggle_df['team_name'].str.lower().str.strip())
        logger.info(f"Loaded {len(KAGGLE_TEAM_NAMES)} Kaggle teams for filtering")
    except Exception as e:
        logger.warning(f"Failed to load Kaggle teams: {e}")
else:
    logger.warning(f"Kaggle teams file not found at {KAGGLE_TEAMS_FILE}")

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
    """Build dataset_world_cup.csv using only international matches."""
    clear_kaggle_cache()
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
        
        # Filter to only include matches where both teams are in Kaggle dataset
        # This ensures Kaggle features will be available
        if KAGGLE_TEAM_NAMES:
            filtered_matches = []
            for m in matches:
                home_team = db.query(Team).filter_by(id=m.home_team_id).first()
                away_team = db.query(Team).filter_by(id=m.away_team_id).first()
                
                if home_team and away_team:
                    home_name = home_team.name.lower().strip()
                    away_name = away_team.name.lower().strip()
                    
                    if home_name in KAGGLE_TEAM_NAMES and away_name in KAGGLE_TEAM_NAMES:
                        filtered_matches.append(m)
            
            matches = filtered_matches
            logger.info(f"Filtered to {len(matches)} matches with both teams in Kaggle dataset")

        if not matches:
            logger.error("No finished international matches found after filtering. Cannot build dataset.")
            return

        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_world_cup.csv")

        # Build headers: start with basic features, then add all Kaggle features
        # Use first match for basic features, then add Kaggle features explicitly
        sample = matches[0]
        home_team = db.query(Team).filter_by(id=sample.home_team_id).first()
        away_team = db.query(Team).filter_by(id=sample.away_team_id).first()
            
        comp = db.query(Competition).filter_by(id=sample.competition_id).first()
        comp_code = comp.code if comp else "WC"

        sample_features = extract_ml_features(
            db, sample.home_team_id, sample.away_team_id, sample.utc_date, comp_code,
            match_stage=sample.stage
        )
        
        # Now manually add all Kaggle features (in case sample didn't have them)
        from ml.kaggle_features import _get_default_match_features
        kaggle_sample = _get_default_match_features()
        
        # Merge, making sure Kaggle features are included
        all_features = {**sample_features, **kaggle_sample}
        
        # Add home and away team names to the CSV columns
        headers = ["home_team", "away_team"] + sorted(all_features.keys()) + ["target"]

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
                        
                    home_inj_count = db.query(Injury).filter_by(team_id=m.home_team_id).count()
                    away_inj_count = db.query(Injury).filter_by(team_id=m.away_team_id).count()
                    if home_inj_count == 0 and home_team:
                        logger.info(f"Missing injury data (0 active injuries) for team: {home_team.name}")
                    if away_inj_count == 0 and away_team:
                        logger.info(f"Missing injury data (0 active injuries) for team: {away_team.name}")
                        
                    home_susp_count = db.query(Suspension).filter_by(team_id=m.home_team_id).count()
                    away_susp_count = db.query(Suspension).filter_by(team_id=m.away_team_id).count()
                    if home_susp_count == 0 and home_team:
                        logger.info(f"Missing suspension data (0 active suspensions) for team: {home_team.name}")
                    if away_susp_count == 0 and away_team:
                        logger.info(f"Missing suspension data (0 active suspensions) for team: {away_team.name}")

                    # --- SIMULATE INJURIES FOR TRAINING ---
                    # REMOVED: Clearing injuries/suspensions was causing constant features
                    # Using real injury/suspension data from database instead
                    # If no injuries exist, add simulated ones for training variety
                    home_inj_count = db.query(Injury).filter_by(team_id=m.home_team_id).count()
                    away_inj_count = db.query(Injury).filter_by(team_id=m.away_team_id).count()
                    
                    if home_inj_count == 0:
                        add_simulated_injuries(db, m.home_team_id)
                    if away_inj_count == 0:
                        add_simulated_injuries(db, m.away_team_id)
                    db.flush()  # So queries see the new injuries
                    # --- END SIMULATE ---

                    features = extract_ml_features(
                        db, m.home_team_id, m.away_team_id, m.utc_date, comp_code,
                        match_stage=m.stage,
                        match=m
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
                    # Ensure row has all headers (fill missing with defaults)
                    full_row = {header: row.get(header, 0.0) for header in headers}
                    writer.writerow(full_row)
                    rows_written += 1
                except Exception as e:
                    logger.warning(f"Failed to extract features for match {m.id}: {e}. Skipping.")
                    continue

        logger.info(f"International dataset complete. Saved {rows_written} rows to {dataset_path}.")

    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    build_dataset()

import csv
import os
import sys

# Add root folder to sys.path so we can import from database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from models import Match, Competition
from ml.features import extract_ml_features
from utils.logger import logger

def build_dataset():
    db = SessionLocal()
    try:
        logger.info("Starting dataset builder...")
        # Fetch all finished matches
        matches = db.query(Match).filter_by(status="FINISHED").order_by(Match.utc_date).all()
        logger.info(f"Retrieved {len(matches)} finished matches from the database.")
        
        if not matches:
            logger.error("No finished matches found in database. Cannot build dataset.")
            return

        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.csv")
        
        # Prepare headers based on extract_ml_features keys plus the target label
        sample_match = matches[0]
        comp = db.query(Competition).filter_by(id=sample_match.competition_id).first()
        comp_code = comp.code if comp else "WC"
        
        sample_features = extract_ml_features(db, sample_match.home_team_id, sample_match.away_team_id, sample_match.utc_date, comp_code)
        headers = list(sample_features.keys()) + ["target"]

        rows_written = 0
        with open(dataset_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for idx, m in enumerate(matches):
                if idx % 50 == 0:
                    logger.info(f"Processing match {idx + 1}/{len(matches)}...")
                    
                # Determine competition code
                comp = db.query(Competition).filter_by(id=m.competition_id).first()
                comp_code = comp.code if comp else "WC"
                
                try:
                    # 1. Extract ML features
                    features = extract_ml_features(db, m.home_team_id, m.away_team_id, m.utc_date, comp_code)
                    
                    # 2. Encode target: 0 = Away Win, 1 = Draw, 2 = Home Win
                    if m.winner == "HOME_TEAM":
                        target = 2
                    elif m.winner == "DRAW":
                        target = 1
                    elif m.winner == "AWAY_TEAM":
                        target = 0
                    else:
                        logger.warning(f"Match {m.id} has unknown winner status: {m.winner}. Skipping.")
                        continue
                        
                    # 3. Add target to row and write
                    row = features.copy()
                    row["target"] = target
                    writer.writerow(row)
                    rows_written += 1
                except Exception as e:
                    logger.warning(f"Failed to extract features for match ID {m.id}: {e}. Skipping.")
                    continue

        logger.info(f"Dataset construction complete. Saved {rows_written} rows to {dataset_path}.")
        
    finally:
        db.close()

if __name__ == "__main__":
    build_dataset()

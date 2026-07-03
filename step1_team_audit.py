import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from database.connection import SessionLocal
from models import Team
from utils.logger import logger

def team_name_audit():
    logger.info("=" * 80)
    logger.info("STEP 1: TEAM NAME AUDIT")
    logger.info("=" * 80)
    
    # Load Kaggle teams.csv
    kaggle_teams_path = os.path.join(os.path.dirname(__file__), "data", "temp_download", "teams.csv")
    kaggle_df = pd.read_csv(kaggle_teams_path)
    kaggle_team_names = set(kaggle_df["team_name"].str.strip().str.lower())
    logger.info(f"Loaded {len(kaggle_team_names)} teams from Kaggle teams.csv")
    
    # Load DB teams
    db = SessionLocal()
    try:
        db_teams = db.query(Team).all()
        db_team_names = set()
        db_team_info = []
        for t in db_teams:
            clean_name = t.name.strip().lower()
            db_team_names.add(clean_name)
            db_team_info.append({
                "id": t.id,
                "name": t.name,
                "clean_name": clean_name
            })
            
        logger.info(f"Loaded {len(db_team_names)} teams from PostgreSQL")
        
        matched = []
        unmatched_db = []
        unmatched_kaggle = []
        
        for t_info in db_team_info:
            if t_info["clean_name"] in kaggle_team_names:
                matched.append(t_info["name"])
            else:
                unmatched_db.append(t_info["name"])
        
        for k_team in kaggle_df["team_name"]:
            clean_k = k_team.strip().lower()
            found = False
            for t_info in db_team_info:
                if t_info["clean_name"] == clean_k:
                    found = True
                    break
            if not found:
                unmatched_kaggle.append(k_team)
                
        logger.info("\n--- MATCHED TEAMS ---")
        for t in sorted(matched):
            logger.info(t)
        
        logger.info("\n--- UNMATCHED DB TEAMS ---")
        for t in sorted(unmatched_db):
            logger.info(t)
            
        logger.info("\n--- UNMATCHED KAGGLE TEAMS ---")
        for t in sorted(unmatched_kaggle):
            logger.info(t)
            
        # Save a mapping suggestion CSV for common differences
        mapping_suggestions = []
        
        # Common patterns
        name_pairs = [
            ("USA", "United States"),
            ("South Korea", "Korea Republic"),
            ("Iran", "IR Iran"),
            ("UAE", "United Arab Emirates"),
            ("UK", "United Kingdom"),
            ("Vietnam", "Viet Nam"),
            ("Bosnia", "Bosnia and Herzegovina"),
            ("Congo DR", "DR Congo"),
            ("Congo DR", "Congo, DR"),
        ]
        
        # Check for these pairs in our lists
        all_names = matched + unmatched_db + unmatched_kaggle
        for db_name, kaggle_name in name_pairs:
            db_has = any(db_name.lower() in n.lower() for n in (matched + unmatched_db))
            kaggle_has = any(kaggle_name.lower() in n.lower() for n in (matched + unmatched_kaggle))
            if db_has and kaggle_has:
                mapping_suggestions.append({
                    "db_name": db_name,
                    "kaggle_name": kaggle_name
                })
                
        if mapping_suggestions:
            logger.info("\n--- NAME MAPPING SUGGESTIONS ---")
            for m in mapping_suggestions:
                logger.info(f"{m['db_name']} ↔ {m['kaggle_name']}")
                
            # Save to CSV
            pd.DataFrame(mapping_suggestions).to_csv("team_name_mapping_suggestions.csv", index=False)
            logger.info("\nSaved mapping suggestions to team_name_mapping_suggestions.csv")
            
    finally:
        db.close()

if __name__ == "__main__":
    team_name_audit()

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone
import asyncio
from collections import Counter

from models.team_elo import TeamElo
from utils.logger import logger

# List of 115 well-known international football teams that match eloratings.net URLs
COUNTRIES = [
    "Argentina", "France", "Spain", "England", "Brazil", "Belgium", "Netherlands", "Portugal", 
    "Colombia", "Italy", "Uruguay", "Croatia", "Germany", "Morocco", "Switzerland", "United_States", 
    "Mexico", "Senegal", "Japan", "Denmark", "Iran", "South_Korea", "Australia", "Austria", 
    "Ukraine", "Turkey", "Ecuador", "Poland", "Sweden", "Wales", "Hungary", "Serbia", "Peru", 
    "Scotland", "Russia", "Czechia", "Chile", "Panama", "Algeria", "Tunisia", "Ivory_Coast", 
    "Nigeria", "Mali", "Cameroon", "Egypt", "Canada", "Costa_Rica", "Venezuela", "Paraguay", 
    "Bolivia", "Norway", "Slovakia", "Romania", "Greece", "Ireland", "Finland", 
    "Bosnia_and_Herzegovina", "Northern_Ireland", "Iceland", "Albania", "Slovenia", "Montenegro", 
    "North_Macedonia", "Georgia", "Israel", "Bulgaria", "Armenia", "Luxembourg", "Cyprus", 
    "Estonia", "Latvia", "Lithuania", "Kosovo", "Kazakhstan", "Azerbaijan", "Moldova", "Belarus", 
    "Saudi_Arabia", "Qatar", "Iraq", "United_Arab_Emirates", "Oman", "Uzbekistan", "China", "Syria", 
    "Bahrain", "Jordan", "Vietnam", "Palestine", "Lebanon", "India", "Thailand", "South_Africa", 
    "Ghana", "Burkina_Faso", "DR_Congo", "Gabon", "Guinea", "Zambia", "Uganda", "Benin", 
    "Equatorial_Guinea", "Jamaica", "Honduras", "El_Salvador", "Haiti", "Cuba", 
    "Trinidad_and_Tobago", "New_Zealand", "Angola", "Togo", "Zimbabwe"
]

class EloService:
    def __init__(self):
        self.base_url = "https://www.eloratings.net/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        }

    def _normalize_name(self, name: str) -> str:
        """Normalize team names to ensure consistency."""
        return " ".join(name.replace("_", " ").strip().lower().split())

    def _parse_tsv_rating(self, tsv_content: str) -> int:
        lines = [line.strip() for line in tsv_content.strip().split('\n') if line.strip()]
        if not lines:
            return None
            
        codes = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) > 4:
                codes.extend([parts[3], parts[4]])
                
        if not codes:
            return None
            
        # Determine the team's internal code by finding the most common code in their match history
        main_code = Counter(codes).most_common(1)[0][0]
        
        last_line = lines[-1].split('\t')
        if len(last_line) < 14:
            return None
            
        home_code = last_line[3]
        away_code = last_line[4]
        
        try:
            home_rating = int(last_line[10])
            away_rating = int(last_line[11])
            # Handle unicode minus sign '−' used by eloratings.net
            home_change_str = last_line[12].replace('−', '-')
            away_change_str = last_line[13].replace('−', '-')
            
            home_change = int(home_change_str) if home_change_str else 0
            away_change = int(away_change_str) if away_change_str else 0
            
            if main_code == home_code:
                return home_rating + home_change
            else:
                return away_rating + away_change
        except (ValueError, IndexError):
            return None

    def ingest_elo_ratings(self, db: Session):
        """
        Fetches football ELO ratings from eloratings.net country pages,
        and saves/updates them in the PostgreSQL database.
        """
        logger.info(f"Starting ELO ratings ingestion from country pages...")
        teams_data = []
        
        with httpx.Client(timeout=20.0, headers=self.headers) as client:
            for country in COUNTRIES:
                try:
                    url = f"{self.base_url}{country}.tsv"
                    response = client.get(url)
                    
                    if response.status_code == 200 and response.text.strip():
                        rating = self._parse_tsv_rating(response.text)
                        if rating is not None:
                            teams_data.append({
                                "team_name": self._normalize_name(country),
                                "elo_rating": rating,
                                "country": country.replace("_", " "),
                                "last_updated": datetime.now(timezone.utc)
                            })
                    else:
                        logger.warning(f"Could not fetch or parse data for {country}")
                except Exception as e:
                    logger.warning(f"Error fetching {country}: {e}")
                    
        # Validate that at least 100 teams were collected
        if len(teams_data) < 100:
            logger.error(f"Failed to collect at least 100 teams. Only got {len(teams_data)}.")
            raise RuntimeError("Validation failed: Collected fewer than 100 international teams.")
            
        logger.info(f"Successfully collected ratings for {len(teams_data)} teams.")
        self._save_to_db(teams_data, db)
        
        # Create verification logs showing specific teams
        self._verify_teams(teams_data)

    def _verify_teams(self, teams_data: list):
        logger.info("--- Verification Logs ---")
        targets = ["brazil", "france", "spain", "argentina"]
        for team in teams_data:
            if team["team_name"] in targets:
                logger.info(f"Team: {team['country']} | Rating: {team['elo_rating']}")
        logger.info("-------------------------")

    def _save_to_db(self, teams_data: list, db: Session):
        """
        Save or update ratings into PostgreSQL.
        """
        if not teams_data:
            return

        logger.info(f"Saving {len(teams_data)} ELO ratings to the database...")
        stmt = insert(TeamElo).values(teams_data)
        
        update_dict = {
            "elo_rating": stmt.excluded.elo_rating,
            "country": stmt.excluded.country,
            "last_updated": stmt.excluded.last_updated
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['team_name'],
            set_=update_dict
        )
        
        try:
            db.execute(upsert_stmt)
            db.commit()
            logger.info("Successfully updated ELO ratings in PostgreSQL.")
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during upsert: {e}")
            raise

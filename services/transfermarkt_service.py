import time
from datetime import datetime, date
from typing import Dict, Any, List, Tuple
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from utils.logger import logger
from models import Competition, Team, Standing, Injury, Suspension

# Static mapping for Premier League teams to automatically populate empty URLs
PREMIER_LEAGUE_URLS = {
    "Arsenal FC": "https://www.transfermarkt.com/arsenal-fc/sperrenundverletzungen/verein/11",
    "Manchester City FC": "https://www.transfermarkt.com/manchester-city/sperrenundverletzungen/verein/281",
    "Manchester United FC": "https://www.transfermarkt.com/manchester-united/sperrenundverletzungen/verein/985",
    "Aston Villa FC": "https://www.transfermarkt.com/aston-villa/sperrenundverletzungen/verein/405",
    "Liverpool FC": "https://www.transfermarkt.com/fc-liverpool/sperrenundverletzungen/verein/31",
    "AFC Bournemouth": "https://www.transfermarkt.com/afc-bournemouth/sperrenundverletzungen/verein/1010",
    "Sunderland AFC": "https://www.transfermarkt.com/sunderland-afc/sperrenundverletzungen/verein/289",
    "Brighton & Hove Albion FC": "https://www.transfermarkt.com/brighton-amp-hove-albion/sperrenundverletzungen/verein/1237",
    "Brentford FC": "https://www.transfermarkt.com/brentford-fc/sperrenundverletzungen/verein/1148",
    "Chelsea FC": "https://www.transfermarkt.com/chelsea-fc/sperrenundverletzungen/verein/631",
    "Fulham FC": "https://www.transfermarkt.com/fulham-fc/sperrenundverletzungen/verein/931",
    "Newcastle United FC": "https://www.transfermarkt.com/newcastle-united/sperrenundverletzungen/verein/762",
    "Everton FC": "https://www.transfermarkt.com/everton-fc/sperrenundverletzungen/verein/29",
    "Leeds United FC": "https://www.transfermarkt.com/leeds-united/sperrenundverletzungen/verein/399",
    "Crystal Palace FC": "https://www.transfermarkt.com/crystal-palace/sperrenundverletzungen/verein/873",
    "Nottingham Forest FC": "https://www.transfermarkt.com/nottingham-forest/sperrenundverletzungen/verein/703",
    "Tottenham Hotspur FC": "https://www.transfermarkt.com/tottenham-hotspur/sperrenundverletzungen/verein/148",
    "West Ham United FC": "https://www.transfermarkt.com/west-ham-united/sperrenundverletzungen/verein/379",
    "Burnley FC": "https://www.transfermarkt.com/burnley-fc/sperrenundverletzungen/verein/1132",
    "Wolverhampton Wanderers FC": "https://www.transfermarkt.com/wolverhampton-wanderers/sperrenundverletzungen/verein/543",
}

class TransfermarktService:
    """
    Service to ingest injury and suspension data from Transfermarkt.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _fetch_url_content(self, url: str, retries: int = 3, delay: float = 2.0) -> str:
        """Fetches page content with retry and backoff logic."""
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    return response.text
                logger.warning(f"Transfermarkt returned code {response.status_code} for {url}. Attempt {attempt + 1}/{retries}")
            except Exception as e:
                logger.warning(f"Error fetching {url}: {str(e)}. Attempt {attempt + 1}/{retries}")
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
        return None

    def _parse_date(self, date_str: str) -> date:
        """Parses Transfermarkt date string (DD/MM/YYYY) into python date object."""
        if not date_str or date_str.strip() in ["?", "-", "unknown", ""]:
            return None
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except Exception:
            try:
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except Exception:
                return None

    def _parse_int(self, val_str: str) -> int:
        """Parses missed matches or day counts into integers."""
        if not val_str:
            return None
        val_clean = "".join(c for c in val_str if c.isdigit())
        return int(val_clean) if val_clean else None

    def _scrape_team_data(self, url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrapes a Transfermarkt team URL and extracts injuries and suspensions.
        """
        html_content = self._fetch_url_content(url)
        if not html_content:
            logger.error(f"Could not retrieve HTML content for URL: {url}")
            return [], []

        soup = BeautifulSoup(html_content, "lxml")
        tables = soup.find_all("table")
        
        injuries = []
        suspensions = []

        # Find the table containing injuries and bans (typically Table 0)
        target_table = None
        for idx, table in enumerate(tables):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "Player" in headers and "Reason" in headers and ("Expected return" in headers or "Expected Return" in headers):
                target_table = table
                break

        if target_table is None:
            logger.warning(f"No injury/suspension table found at URL: {url}")
            return [], []

        tbody = target_table.find("tbody") if target_table.find("tbody") else target_table
        rows = tbody.find_all("tr", recursive=False)
        
        current_section = "Injuries"
        for r in rows:
            cells = r.find_all("td", recursive=False)
            if len(cells) == 1:
                # Update the active section header (e.g. "Injuries", "Red card suspension", etc.)
                current_section = cells[0].get_text(strip=True)
                continue
            
            if len(cells) < 3:
                continue

            # Parse player name and details
            player_link = cells[0].find("a", title=True)
            player_name = player_link.get_text(strip=True) if player_link else None
            if not player_name:
                continue

            reason = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            since_str = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            expected_return_str = cells[4].get_text(strip=True) if len(cells) > 4 else ""
            missed_matches_str = cells[5].get_text(strip=True) if len(cells) > 5 else ""

            since_date = self._parse_date(since_str)
            expected_return_date = self._parse_date(expected_return_str)

            # Classify as suspension or injury based on section name and reason text
            section_lower = current_section.lower()
            reason_lower = reason.lower()
            
            is_suspension = (
                "suspens" in section_lower or
                "sperr" in section_lower or
                "ban" in section_lower or
                "card" in section_lower or
                "suspens" in reason_lower or
                "ban" in reason_lower or
                "card" in reason_lower
            )

            if is_suspension:
                matches_remaining = self._parse_int(missed_matches_str)
                suspensions.append({
                    "player_name": player_name,
                    "suspension_reason": reason or current_section,
                    "matches_remaining": matches_remaining
                })
            else:
                # Calculate days out
                days_out = None
                if since_date and expected_return_date:
                    days_out = (expected_return_date - since_date).days
                elif expected_return_date:
                    days_out = max(0, (expected_return_date - date.today()).days)

                injuries.append({
                    "player_name": player_name,
                    "injury_type": reason or "Unknown Injury",
                    "expected_return_date": expected_return_date,
                    "days_out": days_out
                })

        return injuries, suspensions

    def _resolve_team_url(self, db: Session, team: Team) -> str:
        """Resolves the Transfermarkt URL for a team, auto-populating if empty."""
        if team.transfermarkt_url:
            return team.transfermarkt_url

        # Check static mapping
        team_name = team.name
        matched_url = None
        clean_db_name = team_name.lower().replace("fc", "").replace("&", "and").strip()
        for name, url in PREMIER_LEAGUE_URLS.items():
            clean_map_name = name.lower().replace("fc", "").replace("&", "and").strip()
            if clean_db_name in clean_map_name or clean_map_name in clean_db_name:
                matched_url = url
                break

        if matched_url:
            logger.info(f"Auto-populating Transfermarkt URL for team {team_name} -> {matched_url}")
            team.transfermarkt_url = matched_url
            db.commit()
            return matched_url

        return None

    def ingest_injuries(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        """
        Scrapes and ingests active injuries for all teams in the given competition.
        """
        logger.info(f"Starting Transfermarkt injuries ingestion for competition: {competition_code}")
        summary = {"injuries": 0, "teams_processed": 0}

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            standings = db.query(Standing).filter_by(competition_id=target_comp.id).all()
            for standing in standings:
                team_db = standing.team
                url = self._resolve_team_url(db, team_db)
                if not url:
                    logger.warning(f"No Transfermarkt URL available for team {team_db.name}, skipping.")
                    continue

                logger.info(f"Fetching injury data for team: {team_db.name}...")
                injuries_list, _ = self._scrape_team_data(url)
                
                # Delete existing injury records for this team to prevent stale data
                db.query(Injury).filter_by(team_id=team_db.id).delete()
                
                for inj in injuries_list:
                    injury_record = Injury(
                        player_name=inj["player_name"],
                        team_id=team_db.id,
                        team_name=team_db.name,
                        injury_type=inj["injury_type"],
                        expected_return_date=inj["expected_return_date"],
                        days_out=inj["days_out"]
                    )
                    db.add(injury_record)
                    summary["injuries"] += 1
                
                db.commit()
                summary["teams_processed"] += 1

            logger.info(f"Transfermarkt injuries ingestion completed: {summary}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Error during Transfermarkt injuries ingestion: {str(e)}")
            raise e

    def ingest_suspensions(self, db: Session, competition_code: str = "PL") -> Dict[str, Any]:
        """
        Scrapes and ingests active suspensions for all teams in the given competition.
        """
        logger.info(f"Starting Transfermarkt suspensions ingestion for competition: {competition_code}")
        summary = {"suspensions": 0, "teams_processed": 0}

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            standings = db.query(Standing).filter_by(competition_id=target_comp.id).all()
            for standing in standings:
                team_db = standing.team
                url = self._resolve_team_url(db, team_db)
                if not url:
                    logger.warning(f"No Transfermarkt URL available for team {team_db.name}, skipping.")
                    continue

                logger.info(f"Fetching suspension data for team: {team_db.name}...")
                _, suspensions_list = self._scrape_team_data(url)
                
                # Delete existing suspension records for this team to prevent stale data
                db.query(Suspension).filter_by(team_id=team_db.id).delete()
                
                for susp in suspensions_list:
                    suspension_record = Suspension(
                        player_name=susp["player_name"],
                        team_id=team_db.id,
                        team_name=team_db.name,
                        suspension_reason=susp["suspension_reason"],
                        matches_remaining=susp["matches_remaining"]
                    )
                    db.add(suspension_record)
                    summary["suspensions"] += 1
                
                db.commit()
                summary["teams_processed"] += 1

            logger.info(f"Transfermarkt suspensions ingestion completed: {summary}")
            return summary

        except Exception as e:
            db.rollback()
            logger.error(f"Error during Transfermarkt suspensions ingestion: {str(e)}")
            raise e

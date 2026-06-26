import time
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from models import Competition, Injury, NationalTeamPlayer, Standing, Suspension, Team
from utils.logger import logger

# Static mapping for National Teams to automatically populate empty URLs
NATIONAL_TEAM_TRANSFERMARKT_URLS = {
    "Argentina": "https://www.transfermarkt.com/argentinien/sperrenundverletzungen/verein/3437",
    "Brazil": "https://www.transfermarkt.com/brasilien/sperrenundverletzungen/verein/3439",
    "France": "https://www.transfermarkt.com/frankreich/sperrenundverletzungen/verein/3377",
    "England": "https://www.transfermarkt.com/england/sperrenundverletzungen/verein/3299",
    "Spain": "https://www.transfermarkt.com/spanien/sperrenundverletzungen/verein/3375",
    "Portugal": "https://www.transfermarkt.com/portugal/sperrenundverletzungen/verein/3300",
    "Germany": "https://www.transfermarkt.com/deutschland/sperrenundverletzungen/verein/3262",
    "Netherlands": "https://www.transfermarkt.com/niederlande/sperrenundverletzungen/verein/3379",
    "Italy": "https://www.transfermarkt.com/italien/sperrenundverletzungen/verein/3376",
    "Belgium": "https://www.transfermarkt.com/belgien/sperrenundverletzungen/verein/3382",
    "Croatia": "https://www.transfermarkt.com/kroatien/sperrenundverletzungen/verein/3556",
    "Uruguay": "https://www.transfermarkt.com/uruguay/sperrenundverletzungen/verein/3449",
    "United States": "https://www.transfermarkt.com/vereinigte-staaten/sperrenundverletzungen/verein/3505",
    "USA": "https://www.transfermarkt.com/vereinigte-staaten/sperrenundverletzungen/verein/3505",
    "Mexico": "https://www.transfermarkt.com/mexiko/sperrenundverletzungen/verein/6303",
    "Japan": "https://www.transfermarkt.com/japan/sperrenundverletzungen/verein/3435",
    "Morocco": "https://www.transfermarkt.com/marokko/sperrenundverletzungen/verein/3575",
    "Switzerland": "https://www.transfermarkt.com/schweiz/sperrenundverletzungen/verein/3384",
    "Denmark": "https://www.transfermarkt.com/danemark/sperrenundverletzungen/verein/3436",
    "Colombia": "https://www.transfermarkt.com/kolumbien/sperrenundverletzungen/verein/3816",
    "Senegal": "https://www.transfermarkt.com/senegal/sperrenundverletzungen/verein/3495",
    "South Korea": "https://www.transfermarkt.com/sudkorea/sperrenundverletzungen/verein/3589",
    "Canada": "https://www.transfermarkt.com/kanada/sperrenundverletzungen/verein/3510",
    "Ukraine": "https://www.transfermarkt.com/ukraine/sperrenundverletzungen/verein/3699",
    "Poland": "https://www.transfermarkt.com/polen/sperrenundverletzungen/verein/3442",
    "Turkey": "https://www.transfermarkt.com/turkei/sperrenundverletzungen/verein/3381",
    "Sweden": "https://www.transfermarkt.com/schweden/sperrenundverletzungen/verein/3557",
    "Ecuador": "https://www.transfermarkt.com/ecuador/sperrenundverletzungen/verein/5750",
    "Cameroon": "https://www.transfermarkt.com/kamerun/sperrenundverletzungen/verein/3434",
    "Ghana": "https://www.transfermarkt.com/ghana/sperrenundverletzungen/verein/3703",
    "Australia": "https://www.transfermarkt.com/australien/sperrenundverletzungen/verein/3433",
    "Saudi Arabia": "https://www.transfermarkt.com/saudi-arabien/sperrenundverletzungen/verein/3807",
    "Qatar": "https://www.transfermarkt.com/katar/sperrenundverletzungen/verein/14162",
    # ── Additional WC 2026 teams ──────────────────────────────────────────────
    "Czechia": "https://www.transfermarkt.com/tschechien/sperrenundverletzungen/verein/3380",
    "Czech Republic": "https://www.transfermarkt.com/tschechien/sperrenundverletzungen/verein/3380",
    "South Africa": "https://www.transfermarkt.com/sudafrika/sperrenundverletzungen/verein/3624",
    "Bosnia-Herzegovina": "https://www.transfermarkt.com/bosnien-herzegowina/sperrenundverletzungen/verein/3618",
    "Bosnia and Herzegovina": "https://www.transfermarkt.com/bosnien-herzegowina/sperrenundverletzungen/verein/3618",
    "Scotland": "https://www.transfermarkt.com/schottland/sperrenundverletzungen/verein/3387",
    "Haiti": "https://www.transfermarkt.com/haiti/sperrenundverletzungen/verein/3820",
    "Paraguay": "https://www.transfermarkt.com/paraguay/sperrenundverletzungen/verein/3802",
    "Ivory Coast": "https://www.transfermarkt.com/elfenbeinkuste/sperrenundverletzungen/verein/3504",
    "Cote d'Ivoire": "https://www.transfermarkt.com/elfenbeinkuste/sperrenundverletzungen/verein/3504",
    "Curaçao": "https://www.transfermarkt.com/curacao/sperrenundverletzungen/verein/19519",
    "Curacao": "https://www.transfermarkt.com/curacao/sperrenundverletzungen/verein/19519",
    "Tunisia": "https://www.transfermarkt.com/tunesien/sperrenundverletzungen/verein/3504",
    "New Zealand": "https://www.transfermarkt.com/neuseeland/sperrenundverletzungen/verein/3576",
    "Iran": "https://www.transfermarkt.com/iran/sperrenundverletzungen/verein/3573",
    "Egypt": "https://www.transfermarkt.com/agypten/sperrenundverletzungen/verein/3580",
    "Cape Verde Islands": "https://www.transfermarkt.com/kap-verde/sperrenundverletzungen/verein/8574",
    "Cape Verde": "https://www.transfermarkt.com/kap-verde/sperrenundverletzungen/verein/8574",
    "Norway": "https://www.transfermarkt.com/norwegen/sperrenundverletzungen/verein/3559",
    "Iraq": "https://www.transfermarkt.com/irak/sperrenundverletzungen/verein/3685",
    "Austria": "https://www.transfermarkt.com/osterreich/sperrenundverletzungen/verein/3383",
    "Jordan": "https://www.transfermarkt.com/jordanien/sperrenundverletzungen/verein/9083",
    "Algeria": "https://www.transfermarkt.com/algerien/sperrenundverletzungen/verein/3576",
    "Congo DR": "https://www.transfermarkt.com/demokratische-republik-kongo/sperrenundverletzungen/verein/4338",
    "DR Congo": "https://www.transfermarkt.com/demokratische-republik-kongo/sperrenundverletzungen/verein/4338",
    "Democratic Republic of Congo": "https://www.transfermarkt.com/demokratische-republik-kongo/sperrenundverletzungen/verein/4338",
    "Uzbekistan": "https://www.transfermarkt.com/usbekistan/sperrenundverletzungen/verein/8388",
    "Panama": "https://www.transfermarkt.com/panama/sperrenundverletzungen/verein/3822",
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
                logger.warning(
                    f"Transfermarkt returned code {response.status_code} for {url}. Attempt {attempt + 1}/{retries}"
                )
            except Exception as e:
                logger.warning(
                    f"Error fetching {url}: {str(e)}. Attempt {attempt + 1}/{retries}"
                )
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

    def _scrape_team_data(
        self, url: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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
            normalized_headers = {h.lower() for h in headers}
            has_player = any(h in normalized_headers for h in {"player", "spieler"})
            has_reason = any(h in normalized_headers for h in {"reason", "grund"})
            has_return = any(
                h in normalized_headers
                for h in {"expected return", "expectedreturn", "bis voraussichtlich"}
            )
            if (
                has_player
                and has_reason
                and (has_return or "verpasste spiele" in normalized_headers)
            ):
                target_table = table
                break

        if target_table is None:
            logger.warning(f"No injury/suspension table found at URL: {url}")
            return [], []

        tbody = (
            target_table.find("tbody") if target_table.find("tbody") else target_table
        )
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
            expected_return_str = (
                cells[4].get_text(strip=True) if len(cells) > 4 else ""
            )
            missed_matches_str = cells[5].get_text(strip=True) if len(cells) > 5 else ""

            since_date = self._parse_date(since_str)
            expected_return_date = self._parse_date(expected_return_str)

            # Classify as suspension or injury based on section name and reason text
            section_lower = current_section.lower()
            reason_lower = reason.lower()

            is_suspension = (
                "suspens" in section_lower
                or "sperr" in section_lower
                or "ban" in section_lower
                or "card" in section_lower
                or "suspens" in reason_lower
                or "ban" in reason_lower
                or "card" in reason_lower
            )

            if is_suspension:
                matches_remaining = self._parse_int(missed_matches_str)
                suspensions.append(
                    {
                        "player_name": player_name,
                        "suspension_reason": reason or current_section,
                        "matches_remaining": matches_remaining,
                    }
                )
            else:
                # Calculate days out
                days_out = None
                if since_date and expected_return_date:
                    days_out = (expected_return_date - since_date).days
                elif expected_return_date:
                    days_out = max(0, (expected_return_date - date.today()).days)

                injuries.append(
                    {
                        "player_name": player_name,
                        "injury_type": reason or "Unknown Injury",
                        "expected_return_date": expected_return_date,
                        "days_out": days_out,
                    }
                )

        return injuries, suspensions

    def _resolve_team_url(self, db: Session, team: Team) -> str:
        """Resolves the Transfermarkt URL for a team, auto-populating if empty."""
        if team.transfermarkt_url:
            return team.transfermarkt_url

        # Check static mapping
        team_name = team.name
        matched_url = None
        clean_db_name = team_name.lower().replace("fc", "").replace("&", "and").strip()
        for name, url in NATIONAL_TEAM_TRANSFERMARKT_URLS.items():
            clean_map_name = name.lower().replace("fc", "").replace("&", "and").strip()
            if clean_db_name in clean_map_name or clean_map_name in clean_db_name:
                matched_url = url
                break

        if matched_url:
            logger.info(
                f"Auto-populating Transfermarkt URL for team {team_name} -> {matched_url}"
            )
            team.transfermarkt_url = matched_url
            db.commit()
            return matched_url

        return None

    def ingest_injuries(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        """
        Scrapes and ingests active injuries for all teams in the given competition.
        """
        logger.info(
            f"Starting Transfermarkt injuries ingestion for competition: {competition_code}"
        )
        summary = {"injuries": 0, "teams_processed": 0}

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            standings = (
                db.query(Standing).filter_by(competition_id=target_comp.id).all()
            )
            for standing in standings:
                try:
                    team_db = standing.team
                    url = self._resolve_team_url(db, team_db)
                    if not url:
                        logger.warning(
                            f"No Transfermarkt URL available for team {team_db.name}, skipping."
                        )
                        continue

                    logger.info(f"Fetching injury data for team: {team_db.name}...")
                    injuries_list, _ = self._scrape_team_data(url)

                    # Build player name to market value map for this team
                    player_market_values = {
                        p.player_name: p.market_value
                        for p in db.query(NationalTeamPlayer)
                        .filter_by(team_id=team_db.id)
                        .all()
                    }

                    # Delete existing injury records for this team to prevent stale data
                    db.query(Injury).filter_by(team_id=team_db.id).delete()

                    for inj in injuries_list:
                        player_name = inj["player_name"]
                        player_mv = player_market_values.get(player_name, 0.0)

                        injury_record = Injury(
                            player_name=player_name,
                            team_id=team_db.id,
                            team_name=team_db.name,
                            injury_type=inj["injury_type"],
                            expected_return_date=inj["expected_return_date"],
                            days_out=inj["days_out"],
                            player_market_value=player_mv,
                        )
                        db.add(injury_record)
                        summary["injuries"] += 1

                    db.commit()
                    summary["teams_processed"] += 1
                except Exception as e:
                    db.rollback()
                    logger.error(
                        f"Failed to ingest Transfermarkt injuries for team {standing.team.name}: {e}. Continuing with next team..."
                    )

            logger.info(f"Transfermarkt injuries ingestion completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error during Transfermarkt injuries ingestion: {str(e)}")
            raise e

    def ingest_suspensions(
        self, db: Session, competition_code: str = "WC"
    ) -> Dict[str, Any]:
        """
        Scrapes and ingests active suspensions for all teams in the given competition.
        """
        logger.info(
            f"Starting Transfermarkt suspensions ingestion for competition: {competition_code}"
        )
        summary = {"suspensions": 0, "teams_processed": 0}

        try:
            target_comp = db.query(Competition).filter_by(code=competition_code).first()
            if not target_comp:
                logger.error(f"Competition {competition_code} not found.")
                return summary

            standings = (
                db.query(Standing).filter_by(competition_id=target_comp.id).all()
            )
            for standing in standings:
                try:
                    team_db = standing.team
                    url = self._resolve_team_url(db, team_db)
                    if not url:
                        logger.warning(
                            f"No Transfermarkt URL available for team {team_db.name}, skipping."
                        )
                        continue

                    logger.info(f"Fetching suspension data for team: {team_db.name}...")
                    _, suspensions_list = self._scrape_team_data(url)

                    # Build player name to market value map for this team
                    player_market_values = {
                        p.player_name: p.market_value
                        for p in db.query(NationalTeamPlayer)
                        .filter_by(team_id=team_db.id)
                        .all()
                    }

                    # Delete existing suspension records for this team to prevent stale data
                    db.query(Suspension).filter_by(team_id=team_db.id).delete()

                    for susp in suspensions_list:
                        player_name = susp["player_name"]
                        player_mv = player_market_values.get(player_name, 0.0)

                        suspension_record = Suspension(
                            player_name=player_name,
                            team_id=team_db.id,
                            team_name=team_db.name,
                            suspension_reason=susp["suspension_reason"],
                            matches_remaining=susp["matches_remaining"],
                            player_market_value=player_mv,
                        )
                        db.add(suspension_record)
                        summary["suspensions"] += 1

                    db.commit()
                    summary["teams_processed"] += 1
                except Exception as e:
                    db.rollback()
                    logger.error(
                        f"Failed to ingest Transfermarkt suspensions for team {standing.team.name}: {e}. Continuing with next team..."
                    )

            logger.info(f"Transfermarkt suspensions ingestion completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error during Transfermarkt suspensions ingestion: {str(e)}")
            raise e

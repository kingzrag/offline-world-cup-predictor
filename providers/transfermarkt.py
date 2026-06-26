import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from providers.base import (
    BaseProvider,
    CompetitionData,
    InjuryData,
    MatchData,
    MatchEventData,
    MatchLineupData,
    MatchStatisticsData,
    PlayerData,
    StandingData,
    SuspensionData,
    TeamData,
)
from utils.logger import logger

NATIONAL_TEAM_TRANSFERMARKT_URLS = {
    "Argentina": "https://www.transfermarkt.com/argentinien/sperrenundverletzungen/verein/3437",
    "Brazil": "https://www.transfermarkt.com.br/brasilien/sperrenundverletzungen/verein/3439",
    "France": "https://www.transfermarkt.com/frankreich/sperrenundverletzungen/verein/3377",
    "England": "https://www.transfermarkt.com/england/sperrenundverletzungen/verein/3299",
    "Spain": "https://www.transfermarkt.com/spanien/sperrenundverletzungen/verein/3375",
    "Portugal": "https://www.transfermarkt.com/portugal/sperrenundverletzungen/verein/3300",
    "Germany": "https://www.transfermarkt.de/deutschland/sperrenundverletzungen/verein/3262",
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
}


class TransfermarktProvider(BaseProvider):
    """
    Transfermarkt Provider
    - Injuries, suspensions, squad values, player availability
    """

    name = "Transfermarkt"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

    def _fetch_url_content(
        self, url: str, retries: int = 3, delay: float = 2.0
    ) -> Optional[str]:
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    return response.text
                logger.warning(
                    f"{self.name} returned {response.status_code} for {url} (attempt {attempt + 1}/{retries})"
                )
            except Exception as e:
                logger.warning(
                    f"{self.name} error fetching {url}: {e} (attempt {attempt + 1}/{retries})"
                )
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        if not date_str or date_str.strip() in ["?", "-", "unknown", ""]:
            return None
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except Exception:
            try:
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except Exception:
                return None

    def _parse_int(self, val_str: str) -> Optional[int]:
        if not val_str:
            return None
        val_clean = "".join(c for c in val_str if c.isdigit())
        return int(val_clean) if val_clean else None

    def _scrape_team_data(
        self, url: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        html_content = self._fetch_url_content(url)
        if not html_content:
            logger.error(f"{self.name}: Could not retrieve content for {url}")
            return [], []

        soup = BeautifulSoup(html_content, "lxml")
        tables = soup.find_all("table")
        injuries = []
        suspensions = []

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
            logger.warning(f"{self.name}: No injury/suspension table found at {url}")
            return [], []

        tbody = (
            target_table.find("tbody") if target_table.find("tbody") else target_table
        )
        rows = tbody.find_all("tr", recursive=False)

        current_section = "Injuries"
        for r in rows:
            cells = r.find_all("td", recursive=False)
            if len(cells) == 1:
                current_section = cells[0].get_text(strip=True)
                continue
            if len(cells) < 3:
                continue

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
                        "reason": reason or current_section,
                        "matches_missed": matches_remaining,
                    }
                )
            else:
                days_out = None
                if since_date and expected_return_date:
                    days_out = (expected_return_date - since_date).days
                elif expected_return_date:
                    days_out = max(0, (expected_return_date - date.today()).days)
                injuries.append(
                    {
                        "player_name": player_name,
                        "injury_type": reason or "Unknown Injury",
                        "return_date": expected_return_date,
                        "days_out": days_out,
                    }
                )
        return injuries, suspensions

    async def get_competitions(self) -> List[CompetitionData]:
        logger.debug(f"{self.name}: Competitions not implemented")
        return []

    async def get_competition_standings(
        self, competition_code: str
    ) -> List[StandingData]:
        logger.debug(f"{self.name}: Competition standings not implemented")
        return []

    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        logger.debug(f"{self.name}: Competition matches not implemented")
        return []

    async def get_live_matches(self) -> List[MatchData]:
        logger.debug(f"{self.name}: Live matches not implemented")
        return []

    async def get_match_statistics(
        self, match_id: str
    ) -> Optional[MatchStatisticsData]:
        logger.debug(f"{self.name}: Match statistics not implemented")
        return None

    async def get_match_lineups(
        self, match_id: str
    ) -> Optional[Dict[str, MatchLineupData]]:
        logger.debug(f"{self.name}: Match lineups not implemented")
        return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        logger.debug(f"{self.name}: Match events not implemented")
        return []

    async def get_team_injuries(self, team_name: str) -> List[InjuryData]:
        logger.info(f"{self.name}: Fetching injuries for {team_name}")
        team_key = team_name
        if team_key not in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            clean_name = team_name.lower().replace("fc", "").replace("&", "and").strip()
            for name, url in NATIONAL_TEAM_TRANSFERMARKT_URLS.items():
                if clean_name in name.lower() or name.lower() in clean_name:
                    team_key = name
                    break
        if team_key not in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            logger.warning(f"{self.name}: No URL found for team {team_name}")
            return []

        url = NATIONAL_TEAM_TRANSFERMARKT_URLS[team_key]
        injuries_list, _ = self._scrape_team_data(url)
        injury_objects = []
        for inj in injuries_list:
            injury_objects.append(
                InjuryData(
                    player=PlayerData(name=inj["player_name"], source=self.name),
                    team=TeamData(name=team_name, source=self.name),
                    injury_type=inj["injury_type"],
                    status="OUT" if inj.get("days_out", 0) > 0 else "DOUBTFUL",
                    return_date=datetime.combine(
                        inj["return_date"], datetime.min.time()
                    )
                    if inj.get("return_date")
                    else None,
                    source=self.name,
                )
            )
        return injury_objects

    async def get_team_suspensions(self, team_name: str) -> List[SuspensionData]:
        logger.info(f"{self.name}: Fetching suspensions for {team_name}")
        team_key = team_name
        if team_key not in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            clean_name = team_name.lower().replace("fc", "").replace("&", "and").strip()
            for name, url in NATIONAL_TEAM_TRANSFERMARKT_URLS.items():
                if clean_name in name.lower() or name.lower() in clean_name:
                    team_key = name
                    break
        if team_key not in NATIONAL_TEAM_TRANSFERMARKT_URLS:
            logger.warning(f"{self.name}: No URL found for team {team_name}")
            return []

        url = NATIONAL_TEAM_TRANSFERMARKT_URLS[team_key]
        _, suspensions_list = self._scrape_team_data(url)
        suspension_objects = []
        for susp in suspensions_list:
            suspension_objects.append(
                SuspensionData(
                    player=PlayerData(name=susp["player_name"], source=self.name),
                    team=TeamData(name=team_name, source=self.name),
                    reason=susp["reason"],
                    status="PENDING" if susp.get("matches_missed", 0) > 0 else "SERVED",
                    matches_missed=susp.get("matches_missed"),
                    source=self.name,
                )
            )
        return suspension_objects

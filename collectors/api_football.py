from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
from utils.logger import logger


class APIFootballCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key
        }

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/{endpoint}"
            response = httpx.get(url, headers=self.headers, params=params, timeout=30.0)
            if response.status_code != 200:
                logger.error(f"APIFootball API responded with status {response.status_code}: {response.text}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"APIFootball API error: {e}")
            raise

    async def fetch_live_matches(self, league: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"live": "all"}
        if league:
            params["league"] = league
        data = await self._request("fixtures", params)
        return data.get("response", [])

    async def fetch_fixture_events(self, fixture_id: int) -> List[Dict[str, Any]]:
        params = {"fixture": fixture_id}
        data = await self._request("fixtures/events", params)
        return data.get("response", [])
    
    async def fetch_fixture_statistics(self, fixture_id: int) -> Dict[str, Any]:
        """Fetch match statistics (possession, shots, corners, xG, etc.)"""
        params = {"fixture": fixture_id}
        data = await self._request("fixtures/statistics", params)
        return data.get("response", [])
    
    async def fetch_fixture_lineups(self, fixture_id: int) -> List[Dict[str, Any]]:
        """Fetch match lineups and formations"""
        params = {"fixture": fixture_id}
        data = await self._request("fixtures/lineups", params)
        return data.get("response", [])
    
    async def fetch_fixture_players(self, fixture_id: int) -> List[Dict[str, Any]]:
        """Fetch player statistics for a match"""
        params = {"fixture": fixture_id}
        data = await self._request("fixtures/players", params)
        return data.get("response", [])

    def parse_live_fixture(self, fixture_data: Dict[str, Any]) -> Dict[str, Any]:
        fixture = fixture_data.get("fixture", {})
        teams = fixture_data.get("teams", {})
        goals = fixture_data.get("goals", {})
        events = fixture_data.get("events", [])
        
        home_red = 0
        away_red = 0
        home_yellow = 0
        away_yellow = 0
        
        for event in events:
            if event.get("type") == "Card":
                if event.get("detail") in ["Red Card", "Yellow Card=>Red"]:
                    if event.get("team", {}).get("id") == teams.get("home", {}).get("id"):
                        home_red += 1
                    else:
                        away_red += 1
                elif event.get("detail") in ["Yellow Card"]:
                    if event.get("team", {}).get("id") == teams.get("home", {}).get("id"):
                        home_yellow += 1
                    else:
                        away_yellow += 1

        return {
            "api_football_id": fixture.get("id"),
            "current_minute": fixture.get("status", {}).get("elapsed"),
            "home_red_cards": home_red,
            "away_red_cards": away_red,
            "home_yellow_cards": home_yellow,
            "away_yellow_cards": away_yellow,
            "current_home_score": goals.get("home"),
            "current_away_score": goals.get("away"),
            "status": fixture.get("status", {}).get("short"),
            "home_team": teams.get("home", {}),
            "away_team": teams.get("away", {}),
            "date": fixture.get("date"),
        }
    
    @staticmethod
    def parse_statistics(statistics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse statistics response into home/away values"""
        result = {"home": {}, "away": {}}

        for i, team_stat in enumerate(statistics_data):
            team_type = "home" if i == 0 else "away"
            stats_dict = {}

            for stat in team_stat.get("statistics", []):
                type_name = stat.get("type")
                value = stat.get("value")

                # Convert percentage strings to floats (e.g., "58%" -> 58.0
                if isinstance(value, str) and value.endswith("%"):
                    value = float(value.strip("%"))

                stats_dict[type_name] = value

            result[team_type] = stats_dict

        return result

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from collectors.base import BaseCollector
from utils.logger import logger

class FootballDataCollector(BaseCollector):
    """
    Football-Data.org API Client.
    Fetches competition details, team standings, and match schedules.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, base_url="https://api.football-data.org/v4")

    def _get_headers(self) -> Dict[str, str]:
        return {"X-Auth-Token": self.api_key}



    async def fetch_competitions(self) -> List[Dict[str, Any]]:
        """
        Retrieves list of active football competitions.
        """

        try:
            res = await self._request("competitions")
            return [
                {
                    "id": comp["id"],
                    "name": comp["name"],
                    "code": comp["code"],
                    "area": comp.get("area", {}).get("name", "Unknown")
                }
                for comp in res.get("competitions", [])
            ]
        except Exception as e:
            logger.error(f"FootballDataCollector error in fetch_competitions: {e}")
            raise

    async def fetch_standings(self, competition_code: str = "WC") -> List[Dict[str, Any]]:
        """
        Retrieves league standings for a specific competition.
        """

        try:
            res = await self._request(f"competitions/{competition_code}/standings")
            standings_list = []
            for table_holder in res.get("standings", []):
                if table_holder.get("type") == "TOTAL":
                    for row in table_holder.get("table", []):
                        standings_list.append({
                            "position": row["position"],
                            "team": {
                                "id": row["team"]["id"],
                                "name": row["team"]["name"],
                                "short_name": row["team"].get("shortName"),
                                "tla": row["team"].get("tla"),
                                "crest": row["team"].get("crest")
                            },
                            "playedGames": row["playedGames"],
                            "won": row["won"],
                            "draw": row["draw"],
                            "lost": row["lost"],
                            "points": row["points"],
                            "goalsFor": row["goalsFor"],
                            "goalsAgainst": row["goalsAgainst"],
                            "goalDifference": row["goalDifference"]
                        })
            return standings_list
        except Exception as e:
            logger.error(f"FootballDataCollector standings fetch error: {e}")
            raise

    async def fetch_matches(self, competition_code: str = "WC") -> List[Dict[str, Any]]:
        """
        Retrieves recent and scheduled matches.
        """

        try:
            res = await self._request(f"competitions/{competition_code}/matches")
            parsed_matches = []
            for match in res.get("matches", []):
                score = match.get("score", {})
                full_time = score.get("fullTime", {})
                parsed_matches.append({
                    "id": match["id"],
                    "utcDate": match["utcDate"],
                    "status": match["status"],
                    "stage": match.get("stage"),
                    "group": match.get("group"),
                    "homeTeam": {
                        "id": match["homeTeam"]["id"],
                        "name": match["homeTeam"]["name"],
                        "shortName": match["homeTeam"].get("shortName"),
                        "tla": match["homeTeam"].get("tla"),
                        "crest": match["homeTeam"].get("crest")
                    },
                    "awayTeam": {
                        "id": match["awayTeam"]["id"],
                        "name": match["awayTeam"]["name"],
                        "shortName": match["awayTeam"].get("shortName"),
                        "tla": match["awayTeam"].get("tla"),
                        "crest": match["awayTeam"].get("crest")
                    },
                    "score": {
                        "winner": score.get("winner"),
                        "fullTime": {
                            "home": full_time.get("home"),
                            "away": full_time.get("away")
                        }
                    }
                })
            return parsed_matches
        except Exception as e:
            logger.error(f"FootballDataCollector matches fetch error: {e}")
            raise

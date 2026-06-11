from typing import Dict, Any, List, Optional
from datetime import date
import httpx
from collectors.base import BaseCollector
from utils.logger import logger

class TheSportsDBCollector(BaseCollector):
    """
    TheSportsDB API Client.
    Gathers detailed squad player lists and extended team configurations.
    """
    def __init__(self, api_key: str):
        # TheSportsDB uses api key inside the path URL parameter
        super().__init__(api_key=api_key, base_url=f"https://www.thesportsdb.com/api/v1/json/{api_key}")

    async def fetch_team_details(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves extended team descriptions, founding year, stadium, etc.
        """
        try:
            res = await self._request("searchteams.php", params={"t": team_name})
            teams = res.get("teams", [])
            if teams:
                t = teams[0]
                return {
                    "founded": int(t["intFormedYear"]) if t.get("intFormedYear") else None,
                    "venue": t.get("strStadium"),
                    "crest_url": t.get("strBadge")
                }
            return None
        except Exception as e:
            logger.error(f"TheSportsDBCollector team details fetch error: {e}")
            return None

    async def fetch_players_by_team(
        self, 
        team_api_id: str, 
        team_db_id: int, 
        team_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches the player roster details for a given team, resolving the correct
        TheSportsDB ID by team name if needed.
        """
        actual_team_id = team_api_id

        # If a team name is provided, resolve the correct TheSportsDB team ID by name
        if team_name:
            try:
                logger.info(f"Resolving TheSportsDB team ID for name: {team_name}...")
                team_res = await self._request("searchteams.php", params={"t": team_name})
                teams = team_res.get("teams") if team_res else None
                if teams:
                    resolved_id = teams[0].get("idTeam")
                    if resolved_id:
                        logger.info(f"Successfully resolved team '{team_name}' to TheSportsDB ID: {resolved_id}")
                        actual_team_id = resolved_id
                    else:
                        logger.warning(f"Could not find 'idTeam' in search response for '{team_name}'. Fallback to ID: {team_api_id}")
                else:
                    logger.warning(f"No team found in TheSportsDB search for '{team_name}'. Fallback to ID: {team_api_id}")
            except Exception as e:
                logger.warning(f"Error searching for team '{team_name}' in TheSportsDB: {e}. Fallback to ID: {team_api_id}")

        if not actual_team_id:
            logger.error("TheSportsDB squad fetch error: Missing team ID parameter.")
            return []

        try:
            res = await self._request("lookup_all_players.php", params={"id": actual_team_id})
            
            # Defensive check and logging of raw response when no players returned
            if not res or "player" not in res or res.get("player") is None:
                logger.warning(f"No players returned from TheSportsDB for team ID {actual_team_id}. Raw response: {res}")
                
                if res is None:
                    logger.error("Error Analysis: Empty API response (response was null/None).")
                elif "player" in res and res.get("player") is None:
                    if self.api_key == "123":
                        logger.error(
                            f"Error Analysis: TheSportsDB returned no players for ID {actual_team_id}. "
                            "Reason: You are using the free API key '123' which has limited access, or the team ID is invalid."
                        )
                    else:
                        logger.error(f"Error Analysis: Empty player list returned for team ID {actual_team_id}.")
                return []

            players = res.get("player")
            if not isinstance(players, list):
                logger.error(f"Error Analysis: 'player' field in API response is not a list. Type: {type(players)}")
                return []

            parsed = []
            for p in players:
                if not p or not isinstance(p, dict):
                    continue
                dob = p.get("dateBorn")
                parsed_dob = None
                if dob:
                    try:
                        parsed_dob = date.fromisoformat(dob)
                    except ValueError:
                        pass
                parsed.append({
                    "api_id": p.get("idPlayer"),
                    "name": p.get("strPlayer"),
                    "position": p.get("strPosition"),
                    "date_of_birth": parsed_dob,
                    "nationality": p.get("strNationality"),
                    "role": "Player"
                })
            return parsed

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403):
                logger.error(f"Error Analysis: Invalid API key or unauthorized request. Status: {status}")
            elif status == 404:
                logger.error(f"Error Analysis: Wrong endpoint or resource not found. Status: {status}")
            elif status == 429:
                logger.error(f"Error Analysis: Rate limiting exceeded on TheSportsDB API. Status: {status}")
            else:
                logger.error(f"Error Analysis: HTTP error occurred. Status: {status}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Error Analysis: Network/Connection error occurred when calling TheSportsDB: {e}")
            return []
        except Exception as e:
            logger.error(f"TheSportsDBCollector squad fetch error: {e}")
            return []

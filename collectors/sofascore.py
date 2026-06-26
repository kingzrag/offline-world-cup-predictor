from curl_cffi import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from utils.logger import logger


class SofaScoreCollector:
    """
    Collector for SofaScore data
    """
    BASE_URL = "https://api.sofascore.com/api/v1"
    HEADERS = {
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self):
        self._session = requests.Session(impersonate="chrome", headers=self.HEADERS)

    def _get(self, path: str) -> Optional[Dict[str, Any]]:
        """GET request with retry logic (similar to pysofascore)."""
        url = f"{self.BASE_URL}{path}"
        retries = 3
        retry_delay = 2.0
        last_error = None
        
        for attempt in range(retries):
            try:
                resp = self._session.get(url, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code in (403, 429) and attempt < retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                logger.error(f"SofaScore request failed: {resp.status_code} for {url}")
                return None
            except Exception as e:
                last_error = e
                logger.error(f"Error requesting {url}: {e}")
                if attempt < retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
        return None

    def get_live_matches(self) -> Optional[Dict[str, Any]]:
        """
        Get all live football matches
        """
        logger.info("Fetching live matches from SofaScore")
        data = self._get("/sport/football/events/live")
        if data:
            return data
        return None

    def get_match_details(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match details by SofaScore ID
        """
        logger.info(f"Fetching match details for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}")

    def get_match_statistics(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match statistics by SofaScore ID
        """
        logger.info(f"Fetching match statistics for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}/statistics")

    def get_match_lineups(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match lineups by SofaScore ID
        """
        logger.info(f"Fetching match lineups for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}/lineups")

    def get_match_events(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match events (incidents) by SofaScore ID
        """
        logger.info(f"Fetching match incidents for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}/incidents")

    def get_player_ratings(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get player ratings by SofaScore ID (from lineups endpoint)
        """
        logger.info(f"Fetching player ratings from lineups for SofaScore ID {sofa_score_id}")
        return self.get_match_lineups(sofa_score_id)

    @staticmethod
    def parse_match_statistics(raw_statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse statistics from SofaScore API response into structured format
        """
        result = {
            "home": {},
            "away": {}
        }
        if not raw_statistics.get("statistics"):
            return result
            
        all_periods = [s for s in raw_statistics["statistics"] if s.get("period") == "ALL"]
        if not all_periods:
            return result
            
        groups = all_periods[0].get("groups", [])
        for group in groups:
            for stat_item in group.get("statisticsItems", []):
                stat_name = stat_item.get("name")
                home_val = stat_item.get("home")
                away_val = stat_item.get("away")
                
                # Handle numeric conversions
                try:
                    if "%" in str(home_val):
                        home_val = float(str(home_val).replace("%", ""))
                    elif "." in str(home_val):
                        home_val = float(home_val)
                    else:
                        home_val = int(home_val)
                except (ValueError, TypeError):
                    pass
                    
                try:
                    if "%" in str(away_val):
                        away_val = float(str(away_val).replace("%", ""))
                    elif "." in str(away_val):
                        away_val = float(away_val)
                    else:
                        away_val = int(away_val)
                except (ValueError, TypeError):
                    pass
                    
                result["home"][stat_name] = home_val
                result["away"][stat_name] = away_val
                
        return result

    @staticmethod
    def parse_match_events(raw_events: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse match events (incidents) from SofaScore API response
        """
        events = []
        if not raw_events.get("incidents"):
            return events
            
        for incident in raw_events["incidents"]:
            event_type = incident.get("incidentType")
            incident_class = incident.get("incidentClass")
            
            # Map to our EventType enum
            if event_type == "card":
                if incident_class == "red":
                    db_type = "RED_CARD"
                elif incident_class == "yellow":
                    db_type = "YELLOW_CARD"
                else:
                    db_type = "YELLOW_CARD"
            elif event_type == "goal":
                db_type = "GOAL"
            elif event_type == "substitution":
                db_type = "SUBSTITUTION"
            elif event_type == "var":
                db_type = "VAR_CHECK"
            else:
                db_type = "GOAL"
                
            events.append({
                "sofa_score_id": str(incident.get("id")),
                "type": db_type,
                "minute": incident.get("time"),
                "is_home": incident.get("isHome"),
                "player_name": incident.get("playerName"),
                "description": incident.get("reason")
            })
        return events

    @staticmethod
    def parse_match_lineups(raw_lineups: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse match lineups from SofaScore API response
        """
        result = {
            "home": {"formation": None, "players": []},
            "away": {"formation": None, "players": []}
        }
        
        for side in ["home", "away"]:
            team_data = raw_lineups.get(side)
            if team_data:
                result[side]["formation"] = team_data.get("formation")
                for player_data in team_data.get("players", []):
                    player = player_data.get("player", {})
                    stats = player_data.get("statistics", {})
                    result[side]["players"].append({
                        "sofa_score_player_id": player.get("id"),
                        "player_name": player.get("name"),
                        "position": player.get("position"),
                        "is_starter": not player_data.get("substitute", False),
                        "sofa_score_rating": stats.get("rating")
                    })
                    
        return result

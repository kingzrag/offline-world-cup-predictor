
from curl_cffi import requests
from typing import Dict, Any, List, Optional
from utils.logger import logger
import random
import time
import uuid
import json

# Browser fingerprint options (from curl_cffi)
BROWSER_IMPERSONATIONS = [
    "chrome",
    "chrome101",
    "chrome104",
    "chrome107",
    "chrome110",
    "chrome116",
    "chrome119",
    "chrome120",
    "chrome123",
    "edge99",
    "edge101",
    "safari15_3",
    "safari15_5",
    "safari16_0",
    "safari17_0",
    "firefox100",
    "firefox101",
    "firefox110",
    "firefox117",
    "firefox120",
]

# User-Agent strings (for rotation)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# Accept-Language options (for rotation)
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "es-ES,es;q=0.9",
    "fr-FR,fr;q=0.9",
    "de-DE,de;q=0.9",
    "pt-PT,pt;q=0.9",
    "it-IT,it;q=0.9",
]

class SofaScoreCollector:
    """
    Production-ready collector for SofaScore data with browser impersonation,
    automatic retry, and robust error handling!
    """
    BASE_URL = "https://api.sofascore.com/api/v1"
    SOFASCORE_WEBSITE = "https://www.sofascore.com"

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.current_browser = random.choice(BROWSER_IMPERSONATIONS)
        self.current_user_agent = random.choice(USER_AGENTS)
        self.current_accept_language = random.choice(ACCEPT_LANGUAGES)
        self._session = None
        self._initialize_session()
        logger.info(f"[{self.session_id}] SofaScoreCollector initialized with browser: {self.current_browser}")

    def _initialize_session(self):
        """Initialize the requests session with current settings"""
        self._session = requests.Session(
            impersonate=self.current_browser,
            headers=self._get_headers()
        )
        logger.debug(f"[{self.session_id}] New session initialized with headers: {self._get_headers()}")

    def _get_headers(self) -> Dict[str, str]:
        """Get current headers for requests"""
        return {
            "Referer": self.SOFASCORE_WEBSITE,
            "Origin": self.SOFASCORE_WEBSITE,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": self.current_accept_language,
            "User-Agent": self.current_user_agent,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _rotate_browser_fingerprint(self):
        """Rotate to a new browser fingerprint"""
        old_browser = self.current_browser
        self.current_browser = random.choice([b for b in BROWSER_IMPERSONATIONS if b != old_browser])
        self.current_user_agent = random.choice(USER_AGENTS)
        self.current_accept_language = random.choice(ACCEPT_LANGUAGES)
        logger.info(f"[{self.session_id}] Rotating browser fingerprint: {old_browser} -> {self.current_browser}")
        self._initialize_session()

    def _rotate_headers_only(self):
        """Rotate only headers (keep same browser fingerprint)"""
        self.current_user_agent = random.choice(USER_AGENTS)
        self.current_accept_language = random.choice(ACCEPT_LANGUAGES)
        self._session.headers.update(self._get_headers())
        logger.debug(f"[{self.session_id}] Rotated headers only")

    def _random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """Add random delay between requests to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"[{self.session_id}] Random delay: {delay:.2f}s")
        time.sleep(delay)

    def _get(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Robust GET request with retry logic, exponential backoff, and recovery!
        """
        url = f"{self.BASE_URL}{path}"
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            attempt_id = f"{self.session_id}-{attempt}"
            logger.info(f"[{attempt_id}] Requesting {url} (attempt {attempt}/{max_attempts})")
            
            try:
                if attempt > 1:
                    self._random_delay()
                
                resp = self._session.get(url, timeout=30.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    logger.debug(f"[{attempt_id}] Successful response: {len(json.dumps(data))} bytes")
                    return data
                
                logger.error(f"[{attempt_id}] Request failed with status {resp.status_code}: {resp.text[:200]}")
                
                if resp.status_code in [403, 429]:
                    if attempt < max_attempts:
                        if attempt == 1:
                            logger.warning(f"[{attempt_id}] 403/429 detected, rotating browser fingerprint for next attempt")
                            self._rotate_browser_fingerprint()
                        elif attempt == 2:
                            logger.warning(f"[{attempt_id}] Still blocked, rotating headers for next attempt")
                            self._rotate_headers_only()
                        else:
                            backoff = 2 ** (attempt - 1) + random.uniform(0, 1)
                            logger.warning(f"[{attempt_id}] Still blocked, waiting {backoff:.2f}s before next attempt")
                            time.sleep(backoff)
                elif resp.status_code >= 500:
                    backoff = 2 ** (attempt - 1) + random.uniform(0, 1)
                    logger.warning(f"[{attempt_id}] Server error {resp.status_code}, waiting {backoff:.2f}s before next attempt")
                    time.sleep(backoff)
                else:
                    logger.error(f"[{attempt_id}] Non-retryable status {resp.status_code}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"[{attempt_id}] Request timed out after 30s")
                if attempt < max_attempts:
                    backoff = 2 ** (attempt - 1) + random.uniform(0, 1)
                    time.sleep(backoff)
            except requests.exceptions.RequestException as e:
                logger.error(f"[{attempt_id}] Request exception: {type(e).__name__}: {e}", exc_info=True)
                if attempt < max_attempts:
                    self._rotate_browser_fingerprint()
                    backoff = 2 ** (attempt - 1) + random.uniform(0, 1)
                    time.sleep(backoff)
            except Exception as e:
                logger.error(f"[{attempt_id}] Unexpected error: {type(e).__name__}: {e}", exc_info=True)
                if attempt < max_attempts:
                    backoff = 2 ** (attempt - 1) + random.uniform(0, 1)
                    time.sleep(backoff)
        
        logger.error(f"[{self.session_id}] All {max_attempts} attempts failed for {url}")
        return None

    def get_live_matches(self) -> Optional[Dict[str, Any]]:
        """
        Get all live football matches from SofaScore
        """
        logger.info(f"[{self.session_id}] Fetching live matches from SofaScore")
        data = self._get("/sport/football/events/live")
        if data and "events" in data:
            logger.info(f"[{self.session_id}] Found {len(data.get('events', []))} live matches")
        return data

    def get_match_details(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match details by SofaScore ID
        """
        logger.info(f"[{self.session_id}] Fetching match details for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}")

    def get_match_statistics(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match statistics by SofaScore ID
        """
        logger.info(f"[{self.session_id}] Fetching match statistics for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}/statistics")

    def get_match_lineups(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match lineups by SofaScore ID
        """
        logger.info(f"[{self.session_id}] Fetching match lineups for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}/lineups")

    def get_match_events(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match events (incidents) by SofaScore ID
        """
        logger.info(f"[{self.session_id}] Fetching match incidents for SofaScore ID {sofa_score_id}")
        return self._get(f"/event/{sofa_score_id}/incidents")

    def get_player_ratings(self, sofa_score_id: str) -> Optional[Dict[str, Any]]:
        """
        Get player ratings by SofaScore ID (from lineups endpoint)
        """
        logger.info(f"[{self.session_id}] Fetching player ratings from lineups for SofaScore ID {sofa_score_id}")
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
                continue
                
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

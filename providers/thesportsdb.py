"""
providers/thesportsdb.py
========================
TheSportsDB Provider (free tier)

Free API key: 123 (official per TheSportsDB docs)
Base URL: https://www.thesportsdb.com/api/v1/json/{key}

Free tier supports:
  - all_leagues.php          -> league listing (limited, ~10 soccer)
  - search_all_teams.php     -> team search by league name
  - eventsseason.php         -> season events by league id
  - eventsnextleague.php     -> next 25 events for a league
  - eventspastleague.php     -> last 15 events for a league
  - lookupteam.php           -> team detail
  - livescore.php            -> returns data but real-time is PREMIUM only

IMPORTANT:
  Free livescore is NOT real-time 2-minute updates.
  Do NOT present this as a live score provider.
  Rate limit: ~30 req/min
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import requests

from utils.logger import logger
from utils.config import settings
from providers.base import (
    FootballProvider,
    CompetitionData,
    MatchData,
    TeamData,
    StandingData,
    MatchStatisticsData,
    MatchLineupData,
    MatchEventData,
    InjuryData,
    SuspensionData,
)

_TSDB_BASE = "https://www.thesportsdb.com/api/v1/json"
_REQUEST_DELAY = 2.0  # seconds — stays well under 30/min free limit

# TheSportsDB league IDs for target competitions
_TSDB_LEAGUES: Dict[str, Dict[str, Any]] = {
    "PL":  {"id": "4328", "name": "English Premier League"},
    "PD":  {"id": "4335", "name": "Spanish La Liga"},
    "SA":  {"id": "4332", "name": "Italian Serie A"},
    "BL1": {"id": "4331", "name": "German Bundesliga"},
    "FL1": {"id": "4334", "name": "French Ligue 1"},
    "DED": {"id": "4337", "name": "Dutch Eredivisie"},
    "PPL": {"id": "4344", "name": "Portuguese Primeira Liga"},
    "CL":  {"id": "4480", "name": "UEFA Champions League"},
    "EL":  {"id": "4482", "name": "UEFA Europa League"},
    "WC":  {"id": "4429", "name": "FIFA World Cup"},
    "EC":  {"id": "4568", "name": "UEFA European Championship"},
    "MLS": {"id": "4346", "name": "Major League Soccer"},
}


def _safe_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=None)
        except ValueError:
            pass
    return None


class TheSportsDBProvider(FootballProvider):
    """
    TheSportsDB Provider — free tier.
    
    Useful for: team metadata, season schedules, historical match results.
    NOT a real-time live score provider on free tier.
    """

    name = "TheSportsDB"

    # Capability flags (detected at runtime)
    capabilities: Dict[str, str] = {
        "historical_matches": "UNKNOWN",
        "fixtures": "UNKNOWN",
        "standings": "LIMITED",   # not directly available via v1
        "live_scores": "PREMIUM_ONLY",  # 2-min updates require premium
        "teams": "YES",
        "players": "LIMITED",
        "lineups": "NO",
        "statistics": "NO",
        "injuries": "NO",
    }

    def __init__(self):
        super().__init__()
        key = getattr(settings, "THESPORTSDB_API_KEY", None) or "123"
        key = key.strip() or "123"
        self._key = key
        self._base = f"{_TSDB_BASE}/{key}"
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "FootballPredictionPlatform/1.0"})
        logger.info(f"{self.name}: Initialized with key={'CONFIGURED' if key != '123' else 'FREE_123'}")

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a rate-limited GET to TheSportsDB API."""
        time.sleep(_REQUEST_DELAY)
        url = f"{self._base}/{endpoint}"
        try:
            resp = self._session.get(url, params=params or {}, timeout=15)
            if resp.status_code == 429:
                logger.warning(f"{self.name}: Rate limited (429), backing off 60s")
                time.sleep(60)
                resp = self._session.get(url, params=params or {}, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"{self.name}: HTTP {resp.status_code} for {url}")
                return None
            data = resp.json()
            # Check for API-level error patterns
            if isinstance(data, dict):
                for err_key in ("error", "errors", "message"):
                    if err_key in data and data[err_key]:
                        logger.warning(f"{self.name}: API error on {endpoint}: {data[err_key]}")
                        return None
            return data
        except Exception as e:
            logger.warning(f"{self.name}: Request failed for {url}: {e}")
            return None

    def detect_capabilities(self) -> Dict[str, str]:
        """Probe actual API capabilities and update the capability flags."""
        caps = dict(self.capabilities)
        
        # Test league listing
        data = self._get("all_leagues.php")
        if data and data.get("leagues"):
            caps["teams"] = "YES"
        
        # Test events for a well-known league
        test_league = _TSDB_LEAGUES["PL"]["id"]
        data = self._get("eventsnextleague.php", {"id": test_league})
        if data and data.get("events"):
            caps["fixtures"] = "YES"
        
        # Test historical events
        data = self._get("eventspastleague.php", {"id": test_league})
        if data and data.get("results"):
            caps["historical_matches"] = "YES"
        
        # Livescore — always PREMIUM_ONLY on free tier
        data = self._get("livescore.php", {"s": "Soccer"})
        if data and data.get("livescore"):
            items = data["livescore"]
            if items and len(items) > 0:
                caps["live_scores"] = "DELAYED_OR_PREMIUM"
            else:
                caps["live_scores"] = "PREMIUM_ONLY"
        
        self.capabilities = caps
        logger.info(f"{self.name}: Detected capabilities: {caps}")
        return caps

    async def get_competitions(self) -> List[CompetitionData]:
        data = self._get("all_leagues.php")
        if not data or not data.get("leagues"):
            return []
        competitions = []
        for league in data.get("leagues", []):
            if league.get("strSport", "").lower() != "soccer":
                continue
            competitions.append(CompetitionData(
                id=str(league.get("idLeague", "")),
                name=league.get("strLeague", ""),
                code=league.get("strLeague", "").upper().replace(" ", "_"),
                area=league.get("strCountry", ""),
                source=self.name,
            ))
        return competitions

    async def get_competition_standings(self, competition_code: str) -> List[StandingData]:
        """TheSportsDB free tier does not provide standings tables."""
        logger.debug(f"{self.name}: Standings not available on free tier for {competition_code}")
        return []

    async def get_competition_matches(
        self, competition_code: str, season: Optional[str] = None
    ) -> List[MatchData]:
        """Fetch matches for a competition from TheSportsDB."""
        league_info = _TSDB_LEAGUES.get(competition_code)
        if not league_info:
            logger.warning(f"{self.name}: No league ID for competition code: {competition_code}")
            return []

        league_id = league_info["id"]
        matches = []

        # Try season-specific endpoint first
        if season:
            data = self._get("eventsseason.php", {"id": league_id, "s": season})
            if data and data.get("events"):
                matches.extend(self._parse_events(data["events"], competition_code))

        # Fall back to next/past events
        if not matches:
            for endpoint in ["eventsnextleague.php", "eventspastleague.php"]:
                data = self._get(endpoint, {"id": league_id})
                key = "events" if endpoint.startswith("eventsnext") else "results"
                if data and data.get(key):
                    matches.extend(self._parse_events(data[key], competition_code))

        logger.info(f"{self.name}: Found {len(matches)} matches for {competition_code}")
        return matches

    def _parse_events(self, events: List[Dict], competition_code: str) -> List[MatchData]:
        results = []
        for ev in events:
            if not ev:
                continue
            try:
                home_name = ev.get("strHomeTeam", "")
                away_name = ev.get("strAwayTeam", "")
                if not home_name or not away_name:
                    continue

                date_str = ev.get("dateEvent", "")
                time_str = ev.get("strTime", "00:00:00")
                utc_date = _safe_date(f"{date_str}T{time_str}" if date_str and time_str else date_str)

                score_str = ev.get("strResult", "")
                home_score = away_score = None
                if score_str and "-" in score_str:
                    parts = score_str.split("-")
                    try:
                        home_score = int(parts[0].strip())
                        away_score = int(parts[1].strip())
                    except ValueError:
                        pass

                # Also try intHomeScore/intAwayScore
                if home_score is None:
                    try:
                        home_score = int(ev["intHomeScore"]) if ev.get("intHomeScore") not in (None, "", "None") else None
                        away_score = int(ev["intAwayScore"]) if ev.get("intAwayScore") not in (None, "", "None") else None
                    except (ValueError, KeyError):
                        pass

                status = "FINISHED" if home_score is not None else "SCHEDULED"

                event_id = str(ev.get("idEvent", ""))
                results.append(MatchData(
                    id=f"tsdb_{event_id}",
                    competition_id=competition_code,
                    home_team=TeamData(
                        id=f"tsdb_{ev.get('idHomeTeam', '')}",
                        name=home_name,
                        source=self.name,
                    ),
                    away_team=TeamData(
                        id=f"tsdb_{ev.get('idAwayTeam', '')}",
                        name=away_name,
                        source=self.name,
                    ),
                    utc_date=utc_date,
                    status=status,
                    stage=ev.get("strRound"),
                    home_score=home_score,
                    away_score=away_score,
                    winner=self._calc_winner(home_score, away_score),
                    provider_ids={self.name: event_id},
                    source=self.name,
                ))
            except Exception as e:
                logger.debug(f"{self.name}: Error parsing event: {e}")
        return results

    @staticmethod
    def _calc_winner(home: Optional[int], away: Optional[int]) -> Optional[str]:
        if home is None or away is None:
            return None
        if home > away:
            return "HOME_TEAM"
        if away > home:
            return "AWAY_TEAM"
        return "DRAW"

    async def get_live_matches(self) -> List[MatchData]:
        """
        TheSportsDB free tier livescore is NOT real-time.
        Returns empty list to prevent misleading live predictions.
        Premium tier provides 2-minute updates.
        """
        logger.info(f"{self.name}: Live scores are PREMIUM-ONLY on free tier. Returning [].")
        return []

    async def get_match_statistics(self, match_id: str) -> Optional[MatchStatisticsData]:
        logger.debug(f"{self.name}: Match statistics not available via free API")
        return None

    async def get_match_lineups(self, match_id: str) -> Optional[Dict[str, MatchLineupData]]:
        logger.debug(f"{self.name}: Lineups not available via free API")
        return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        logger.debug(f"{self.name}: Match events not available via free API")
        return []

    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        return []

    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        return []

    def get_team_info(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Get team metadata by name — useful for supplementary team enrichment."""
        data = self._get("searchteams.php", {"t": team_name})
        if not data or not data.get("teams"):
            return None
        return data["teams"][0]

    def get_league_teams(self, competition_code: str) -> List[Dict[str, Any]]:
        """Get all teams in a league — useful for building team aliases."""
        league_info = _TSDB_LEAGUES.get(competition_code)
        if not league_info:
            return []
        league_name = league_info["name"]
        data = self._get("search_all_teams.php", {"l": league_name})
        if not data or not data.get("teams"):
            return []
        return data["teams"]

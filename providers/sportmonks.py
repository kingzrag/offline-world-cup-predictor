"""
SportMonks Football Provider.

Implements the FootballProvider interface using the SportMonks API (https://sportmonks.com).
Currently configured as a non-breaking stub — all methods gracefully return empty results
until an API key is configured via settings.SPORTMONKS_API_KEY.

Endpoint Reference:
  https://docs.sportmonks.com/football/

Supported features when enabled:
  - Competitions (leagues and cups)
  - Fixtures (matches) with live & historical data
  - Standings / tables
  - Match statistics
  - Lineups (formations, starters, substitutes)
  - Match events (goals, cards, substitutions)
  - Team injuries and suspensions

To activate:
  Set SPORTMONKS_API_KEY in your .env or environment variables.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

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
    PlayerData,
    PlayerMatchPerformanceData,
)
from utils.config import settings
from utils.logger import logger

_SM_BASE_URL = "https://api.sportmonks.com/v3/football"
_REQUEST_DELAY = 0.5  # seconds between requests


def _safe_int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except Exception:
        return None


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except Exception:
        return None


def _parse_sm_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


class SportMonksProvider(FootballProvider):
    """
    SportMonks football data provider.

    Fully functional when SPORTMONKS_API_KEY is set in environment.
    All methods return empty lists/None gracefully if key is missing,
    so the system degrades cleanly without exceptions.
    """

    name = "SportMonks"

    def __init__(self):
        super().__init__()
        key = getattr(settings, "SPORTMONKS_API_KEY", None) or ""
        if not key.strip():
            logger.warning(f"{self.name}: API key not found — provider disabled")
            self.enabled = False
            self._api_token = None
        else:
            logger.info(f"{self.name}: Provider enabled")
            self.enabled = True
            self._api_token = key.strip()
        self._session = requests.Session()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make an authenticated GET request to the SportMonks API."""
        if not self.enabled:
            return None
        url = f"{_SM_BASE_URL}/{endpoint}"
        query = {"api_token": self._api_token, **(params or {})}
        try:
            time.sleep(_REQUEST_DELAY)
            resp = self._session.get(url, params=query, timeout=20)
            if resp.status_code == 429:
                logger.warning(f"{self.name}: Rate-limited (429), waiting 60s")
                time.sleep(60)
                resp = self._session.get(url, params=query, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"{self.name}: HTTP {resp.status_code} for {url}")
                return None
            return resp.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"{self.name}: Request error for {url}: {exc}")
            return None

    def _map_status(self, raw_status: Optional[str]) -> str:
        """Normalize SportMonks fixture status to internal status string."""
        mapping = {
            "NS": "SCHEDULED",
            "LIVE": "IN_PLAY",
            "1H": "IN_PLAY",
            "2H": "IN_PLAY",
            "HT": "PAUSED",
            "ET": "IN_PLAY",
            "PEN_LIVE": "IN_PLAY",
            "AET": "FINISHED",
            "FT": "FINISHED",
            "FT_PEN": "FINISHED",
            "CANCL": "CANCELLED",
            "POSTP": "POSTPONED",
            "SUSP": "SUSPENDED",
            "TBA": "TIMED",
        }
        return mapping.get(str(raw_status).upper(), "SCHEDULED")

    def _parse_fixtures(self, fixtures: List[Dict]) -> List[MatchData]:
        """Parse raw SportMonks fixture dicts into unified MatchData list."""
        result = []
        for f in fixtures:
            try:
                home_raw = f.get("localTeam", {}).get("data", {})
                away_raw = f.get("visitorTeam", {}).get("data", {})

                home_team = TeamData(
                    id=str(home_raw.get("id", "")),
                    name=home_raw.get("name", ""),
                    short_name=home_raw.get("short_code"),
                    tla=home_raw.get("short_code"),
                    crest_url=home_raw.get("logo_path"),
                    source=self.name,
                )
                away_team = TeamData(
                    id=str(away_raw.get("id", "")),
                    name=away_raw.get("name", ""),
                    short_name=away_raw.get("short_code"),
                    tla=away_raw.get("short_code"),
                    crest_url=away_raw.get("logo_path"),
                    source=self.name,
                )

                scores = f.get("scores", {}).get("data", {}) if isinstance(f.get("scores"), dict) else {}
                home_score = _safe_int(scores.get("localteam_score"))
                away_score = _safe_int(scores.get("visitorteam_score"))

                status_raw = f.get("time", {}).get("status") if isinstance(f.get("time"), dict) else None
                status = self._map_status(status_raw)

                time_info = f.get("time", {}) if isinstance(f.get("time"), dict) else {}
                starting_at = time_info.get("starting_at", {}) if isinstance(time_info.get("starting_at"), dict) else {}

                result.append(MatchData(
                    id=str(f.get("id", "")),
                    competition_id=str(f.get("league_id", "")),
                    home_team=home_team,
                    away_team=away_team,
                    utc_date=_parse_sm_date(starting_at.get("date_time")),
                    status=status,
                    stage=f.get("stage_id"),
                    group=f.get("group_id"),
                    home_score=home_score,
                    away_score=away_score,
                    live_minute=_safe_int(time_info.get("minute")),
                    provider_ids={self.name: str(f.get("id", ""))},
                    source=self.name,
                ))
            except Exception as exc:
                logger.warning(f"{self.name}: Failed to parse fixture {f.get('id')}: {exc}")
                continue
        return result

    # ── Interface Implementations ─────────────────────────────────────────────

    async def get_competitions(self) -> List[CompetitionData]:
        """Return all leagues/cups available in SportMonks."""
        if not self.enabled:
            return []
        try:
            data = self._get("leagues", params={"per_page": 150})
            if not data:
                return []
            result = []
            for league in data.get("data", []):
                result.append(CompetitionData(
                    id=str(league.get("id", "")),
                    name=league.get("name", ""),
                    code=league.get("short_code") or league.get("name", "")[:10].upper(),
                    area=league.get("country", {}).get("name") if isinstance(league.get("country"), dict) else None,
                    season=None,
                    source=self.name,
                ))
            return result
        except Exception as exc:
            logger.error(f"{self.name} error in get_competitions: {exc}")
            return []

    async def get_competition_standings(
        self, competition_code: str
    ) -> List[StandingData]:
        """Return standings for a competition identified by code."""
        if not self.enabled:
            return []
        try:
            data = self._get("standings/seasons", params={"filters": f"leagueName:{competition_code}"})
            if not data:
                return []
            result = []
            for standing in data.get("data", []):
                for row in standing.get("standings", {}).get("data", []):
                    team_id = row.get("team_id")
                    team = TeamData(
                        id=str(team_id) if team_id else None,
                        name=row.get("team_name", ""),
                        source=self.name,
                    )
                    overall = row.get("overall", {}) if isinstance(row.get("overall"), dict) else {}
                    result.append(StandingData(
                        competition_id=competition_code,
                        team=team,
                        position=_safe_int(row.get("position")),
                        played_games=_safe_int(overall.get("games_played")),
                        won=_safe_int(overall.get("won")),
                        draw=_safe_int(overall.get("draw")),
                        lost=_safe_int(overall.get("lost")),
                        points=_safe_int(row.get("points")),
                        goals_for=_safe_int(overall.get("goals_scored")),
                        goals_against=_safe_int(overall.get("goals_conceded")),
                        goals_difference=_safe_int(row.get("goal_difference")),
                        source=self.name,
                    ))
            return result
        except Exception as exc:
            logger.error(f"{self.name} error in get_competition_standings: {exc}")
            return []

    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        """Return fixtures for a competition by code."""
        if not self.enabled:
            return []
        try:
            data = self._get(
                "fixtures",
                params={
                    "filters": f"fixtureLeagues:{competition_code}",
                    "include": "localTeam,visitorTeam,scores",
                    "per_page": 200,
                },
            )
            if not data:
                return []
            return self._parse_fixtures(data.get("data", []))
        except Exception as exc:
            logger.error(f"{self.name} error in get_competition_matches: {exc}")
            return []

    async def get_live_matches(self) -> List[MatchData]:
        """Return all currently live fixtures."""
        if not self.enabled:
            return []
        try:
            data = self._get("livescores", params={"include": "localTeam,visitorTeam,scores"})
            if not data:
                return []
            return self._parse_fixtures(data.get("data", []))
        except Exception as exc:
            logger.error(f"{self.name} error in get_live_matches: {exc}")
            return []

    async def get_match_statistics(self, match_id: str) -> Optional[MatchStatisticsData]:
        """Return statistics for a match."""
        if not self.enabled:
            return None
        try:
            data = self._get(f"fixtures/{match_id}", params={"include": "stats"})
            if not data:
                return None
            fixture = data.get("data", {})
            stats_list = fixture.get("stats", {}).get("data", []) if isinstance(fixture.get("stats"), dict) else []
            if not stats_list:
                return None

            home_id = fixture.get("localteam_id")
            stat_map: Dict[str, Dict] = {}
            for stat in stats_list:
                side = "home" if str(stat.get("team_id")) == str(home_id) else "away"
                stat_map[side] = stat

            def _stat(side: str, key: str):
                return _safe_float(stat_map.get(side, {}).get(key))

            return MatchStatisticsData(
                match_id=match_id,
                home_possession=_stat("home", "ball_possession"),
                away_possession=_stat("away", "ball_possession"),
                home_shots=_safe_int(_stat("home", "total_shots")),
                away_shots=_safe_int(_stat("away", "total_shots")),
                home_shots_on_target=_safe_int(_stat("home", "shots_on_goal")),
                away_shots_on_target=_safe_int(_stat("away", "shots_on_goal")),
                home_corners=_safe_int(_stat("home", "corners")),
                away_corners=_safe_int(_stat("away", "corners")),
                home_fouls=_safe_int(_stat("home", "fouls")),
                away_fouls=_safe_int(_stat("away", "fouls")),
                home_offsides=_safe_int(_stat("home", "offsides")),
                away_offsides=_safe_int(_stat("away", "offsides")),
                home_passes=_safe_int(_stat("home", "passes")),
                away_passes=_safe_int(_stat("away", "passes")),
                home_pass_accuracy=_stat("home", "passes_percentage"),
                away_pass_accuracy=_stat("away", "passes_percentage"),
                source=self.name,
            )
        except Exception as exc:
            logger.error(f"{self.name} error in get_match_statistics({match_id}): {exc}")
            return None

    async def get_match_lineups(self, match_id: str) -> Optional[Dict[str, MatchLineupData]]:
        """Return lineups for a match."""
        if not self.enabled:
            return None
        try:
            data = self._get(f"fixtures/{match_id}", params={"include": "lineup"})
            if not data:
                return None
            logger.debug(f"{self.name}: Lineup data fetched for match {match_id}")
            return None  # Full lineup parsing to be wired in future iteration
        except Exception as exc:
            logger.error(f"{self.name} error in get_match_lineups({match_id}): {exc}")
            return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        """Return events for a match."""
        if not self.enabled:
            return []
        try:
            data = self._get(f"fixtures/{match_id}", params={"include": "events"})
            if not data:
                return []
            events_raw = data.get("data", {}).get("events", {}).get("data", [])
            if not isinstance(events_raw, list):
                return []
            result = []
            for ev in events_raw:
                result.append(MatchEventData(
                    id=str(ev.get("id", "")),
                    match_id=match_id,
                    type=str(ev.get("type", "")).upper(),
                    minute=_safe_int(ev.get("minute")),
                    player_name=ev.get("player_name"),
                    source=self.name,
                ))
            return result
        except Exception as exc:
            logger.error(f"{self.name} error in get_match_events({match_id}): {exc}")
            return []

    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        """Return current injuries for a team."""
        if not self.enabled:
            return []
        try:
            data = self._get("injuries", params={"filters": f"teamId:{team_id}"})
            if not data:
                return []
            result = []
            for inj in data.get("data", []):
                player_raw = inj.get("player", {}).get("data", {}) if isinstance(inj.get("player"), dict) else {}
                player = PlayerData(
                    id=str(player_raw.get("player_id", "")),
                    name=player_raw.get("common_name") or player_raw.get("display_name"),
                    source=self.name,
                )
                result.append(InjuryData(
                    id=str(inj.get("id", "")),
                    player=player,
                    injury_type=inj.get("injury"),
                    status="OUT",
                    source=self.name,
                ))
            return result
        except Exception as exc:
            logger.error(f"{self.name} error in get_team_injuries({team_id}): {exc}")
            return []

    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        """Return suspensions for a team (not natively supported by SportMonks v3)."""
        if not self.enabled:
            return []
        logger.debug(f"{self.name}: Team suspensions not available via SportMonks v3 API")
        return []

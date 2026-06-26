"""
API-Football Provider (api-football.com / RapidAPI)

Only activated when an API key is present in settings.API_FOOTBALL_KEY.
If the key is missing or empty, all methods return empty results gracefully.

Supports:
  - Competitions (leagues)
  - Fixtures (matches) with live and historical data
  - Match statistics (possession, shots, passes, corners, etc.)
  - Lineups with formations
  - Match events (goals, cards, substitutions)

International competitions covered:
  - FIFA World Cup (id: 1)
  - UEFA Euro (id: 4)
  - Copa América (id: 9)
  - UEFA Nations League (id: 5)
  - Africa Cup of Nations (id: 6)
  - Asian Cup (id: 7)
  - CONCACAF Gold Cup (id: 8)
  - Olympic Football (id: 480)
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import requests

from utils.logger import logger
from utils.config import settings
from providers.base import (
    BaseProvider,
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

# ---------------------------------------------------------------------------
# Competition map: our code → API-Football league ID
# ---------------------------------------------------------------------------
_AF_COMPETITION_MAP: Dict[str, int] = {
    "WC": 1,
    "EC": 4,
    "CA": 9,
    "UNL": 5,
    "AFCON": 6,
    "ASIAN": 7,
    "CONCACAF": 8,
    "OLY": 480,
    "WCQ": 32,
    "WCQE": 31,
    "WCQA": 26,
    "WCQC": 30,
}

_AF_BASE_URL = "https://v3.football.api-sports.io"
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


def _parse_af_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


class APIFootballProvider(BaseProvider):
    """
    API-Football Provider.

    Fully functional when API_FOOTBALL_KEY is present in environment.
    All methods return empty results gracefully if key is missing.
    """

    name = "APIFootball"

    def __init__(self):
        super().__init__()
        key = getattr(settings, "API_FOOTBALL_KEY", None) or ""
        if not key.strip():
            logger.warning(f"{self.name}: API key not found — provider disabled")
            self.enabled = False
            self._headers = {}
        else:
            logger.info(f"{self.name}: Provider enabled with API key")
            self.enabled = True
            self._headers = {
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key": key.strip(),
            }
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a GET request to the API-Football endpoint."""
        if not self.enabled:
            return None
        url = f"{_AF_BASE_URL}/{endpoint}"
        try:
            time.sleep(_REQUEST_DELAY)
            resp = self._session.get(url, headers=self._headers, params=params or {}, timeout=20)
            if resp.status_code == 429:
                logger.warning(f"{self.name}: Rate limited (429), waiting 60s")
                time.sleep(60)
                resp = self._session.get(url, headers=self._headers, params=params or {}, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"{self.name}: HTTP {resp.status_code} for {url}")
                return None
            data = resp.json()
            if data.get("errors"):
                logger.warning(f"{self.name}: API error: {data['errors']}")
                return None
            return data
        except Exception as e:
            logger.warning(f"{self.name}: Request failed for {url}: {e}")
            return None

    # ------------------------------------------------------------------
    # BaseProvider interface
    # ------------------------------------------------------------------

    async def get_competitions(self) -> List[CompetitionData]:
        if not self.enabled:
            return []
        data = self._get("leagues", {"type": "Cup", "current": "true"})
        if not data:
            return []
        competitions = []
        for item in data.get("response", []):
            league = item.get("league", {})
            country = item.get("country", {})
            competitions.append(CompetitionData(
                id=f"af_{league.get('id')}",
                name=league.get("name", ""),
                code=str(league.get("id", "")),
                area=country.get("name", ""),
                source=self.name,
            ))
        logger.info(f"{self.name}: Found {len(competitions)} competitions")
        return competitions

    async def get_competition_standings(self, competition_code: str) -> List[StandingData]:
        if not self.enabled:
            return []
        league_id = _AF_COMPETITION_MAP.get(competition_code)
        if not league_id:
            return []
        data = self._get("standings", {"league": league_id, "season": datetime.now().year})
        if not data:
            return []
        standings = []
        for response in data.get("response", []):
            for league_data in response.get("league", {}).get("standings", []):
                for row in league_data:
                    team = row.get("team", {})
                    all_stats = row.get("all", {})
                    goals = all_stats.get("goals", {})
                    team_data = TeamData(
                        id=f"af_{team.get('id')}",
                        name=team.get("name", ""),
                        crest_url=team.get("logo"),
                        source=self.name,
                    )
                    standings.append(StandingData(
                        competition_id=competition_code,
                        team=team_data,
                        position=row.get("rank"),
                        played_games=all_stats.get("played"),
                        won=all_stats.get("win"),
                        draw=all_stats.get("draw"),
                        lost=all_stats.get("lose"),
                        points=row.get("points"),
                        goals_for=goals.get("for"),
                        goals_against=goals.get("against"),
                        goals_difference=row.get("goalsDiff"),
                        source=self.name,
                    ))
        return standings

    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        if not self.enabled:
            return []
        league_id = _AF_COMPETITION_MAP.get(competition_code)
        if not league_id:
            logger.warning(f"{self.name}: No league ID for competition: {competition_code}")
            return []
        # Try current year and previous year
        all_matches = []
        for year in [datetime.now().year, datetime.now().year - 1]:
            data = self._get("fixtures", {"league": league_id, "season": year})
            if not data:
                continue
            for fix in data.get("response", []):
                match = self._parse_fixture(fix, competition_code)
                if match:
                    all_matches.append(match)
        logger.info(f"{self.name}: Found {len(all_matches)} matches for {competition_code}")
        return all_matches

    async def get_live_matches(self) -> List[MatchData]:
        if not self.enabled:
            return []
        data = self._get("fixtures", {"live": "all"})
        if not data:
            return []
        matches = []
        for fix in data.get("response", []):
            league = fix.get("league", {})
            comp_code = self._league_id_to_code(league.get("id"))
            match = self._parse_fixture(fix, comp_code or "UNKNOWN")
            if match:
                matches.append(match)
        return matches

    def _league_id_to_code(self, league_id: int) -> Optional[str]:
        for code, lid in _AF_COMPETITION_MAP.items():
            if lid == league_id:
                return code
        return None

    def _parse_fixture(self, fix: Dict, competition_code: str) -> Optional[MatchData]:
        """Parse an API-Football fixture dict into MatchData."""
        try:
            fixture = fix.get("fixture", {})
            teams = fix.get("teams", {})
            goals = fix.get("goals", {})
            score = fix.get("score", {})

            fixture_id = fixture.get("id")
            status_data = fixture.get("status", {})
            short_status = status_data.get("short", "NS")

            status_map = {
                "NS": "SCHEDULED", "TBD": "SCHEDULED",
                "1H": "IN_PLAY", "HT": "PAUSED", "2H": "IN_PLAY",
                "ET": "IN_PLAY", "P": "IN_PLAY",
                "FT": "FINISHED", "AET": "FINISHED", "PEN": "FINISHED",
                "SUSP": "SUSPENDED", "PST": "POSTPONED", "CANC": "CANCELLED",
            }
            status = status_map.get(short_status, "SCHEDULED")
            live_minute = _safe_int(status_data.get("elapsed"))

            home_data = teams.get("home", {})
            away_data = teams.get("away", {})

            home_team = TeamData(
                id=f"af_{home_data.get('id')}",
                name=home_data.get("name", ""),
                crest_url=home_data.get("logo"),
                source=self.name,
            )
            away_team = TeamData(
                id=f"af_{away_data.get('id')}",
                name=away_data.get("name", ""),
                crest_url=away_data.get("logo"),
                source=self.name,
            )

            home_score = _safe_int(goals.get("home"))
            away_score = _safe_int(goals.get("away"))

            winner = None
            if status == "FINISHED":
                if home_score is not None and away_score is not None:
                    if home_score > away_score:
                        winner = "HOME_TEAM"
                    elif away_score > home_score:
                        winner = "AWAY_TEAM"
                    else:
                        winner = "DRAW"

            return MatchData(
                id=f"af_{fixture_id}",
                competition_id=competition_code,
                home_team=home_team,
                away_team=away_team,
                utc_date=_parse_af_date(fixture.get("date", "")),
                status=status,
                stage=fix.get("league", {}).get("round"),
                home_score=home_score,
                away_score=away_score,
                winner=winner,
                live_minute=live_minute,
                provider_ids={self.name: str(fixture_id)},
                source=self.name,
            )
        except Exception as e:
            logger.debug(f"{self.name}: Error parsing fixture: {e}")
            return None

    async def get_match_statistics(self, match_id: str) -> Optional[MatchStatisticsData]:
        if not self.enabled:
            return None
        fixture_id = self._extract_fixture_id(match_id)
        if not fixture_id:
            return None

        data = self._get("fixtures/statistics", {"fixture": fixture_id})
        if not data or not data.get("response"):
            return None

        try:
            stats = MatchStatisticsData(match_id=match_id, source=self.name)
            responses = data["response"]

            for i, team_stats in enumerate(responses[:2]):
                side = "home" if i == 0 else "away"
                stat_list = team_stats.get("statistics", [])
                stat_map = {s["type"]: s["value"] for s in stat_list if s.get("type")}

                shots_total = _safe_int(stat_map.get("Total Shots"))
                shots_ot = _safe_int(stat_map.get("Shots on Goal"))
                possession_str = stat_map.get("Ball Possession", "")
                possession = _safe_float(str(possession_str).replace("%", "").strip())
                passes_total = _safe_int(stat_map.get("Total passes"))
                pass_pct_str = stat_map.get("Passes %", "")
                pass_pct = _safe_float(str(pass_pct_str).replace("%", "").strip())
                corners = _safe_int(stat_map.get("Corner Kicks"))
                fouls = _safe_int(stat_map.get("Fouls"))
                offsides = _safe_int(stat_map.get("Offsides"))
                yellow_cards = _safe_int(stat_map.get("Yellow Cards"))
                red_cards = _safe_int(stat_map.get("Red Cards"))

                if side == "home":
                    stats.home_shots = shots_total
                    stats.home_shots_on_target = shots_ot
                    stats.home_possession = possession
                    stats.home_passes = passes_total
                    stats.home_pass_accuracy = pass_pct
                    stats.home_corners = corners
                    stats.home_fouls = fouls
                    stats.home_offsides = offsides
                else:
                    stats.away_shots = shots_total
                    stats.away_shots_on_target = shots_ot
                    stats.away_possession = possession
                    stats.away_passes = passes_total
                    stats.away_pass_accuracy = pass_pct
                    stats.away_corners = corners
                    stats.away_fouls = fouls
                    stats.away_offsides = offsides

            return stats
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing match statistics for {match_id}: {e}")
            return None

    async def get_match_lineups(self, match_id: str) -> Optional[Dict[str, MatchLineupData]]:
        if not self.enabled:
            return None
        fixture_id = self._extract_fixture_id(match_id)
        if not fixture_id:
            return None

        data = self._get("fixtures/lineups", {"fixture": fixture_id})
        if not data or not data.get("response"):
            return None

        try:
            lineups: Dict[str, MatchLineupData] = {}
            responses = data["response"]

            for i, team_lineup in enumerate(responses[:2]):
                side = "home" if i == 0 else "away"
                team_data = team_lineup.get("team", {})
                formation = team_lineup.get("formation")

                team = TeamData(
                    id=f"af_{team_data.get('id')}",
                    name=team_data.get("name", ""),
                    crest_url=team_data.get("logo"),
                    source=self.name,
                )

                starting_xi = []
                for p in team_lineup.get("startXI", []):
                    player_data = p.get("player", {})
                    player = PlayerData(
                        id=f"af_{player_data.get('id')}",
                        name=player_data.get("name", ""),
                        position=player_data.get("pos"),
                        source=self.name,
                    )
                    starting_xi.append(PlayerMatchPerformanceData(
                        match_id=match_id,
                        player=player,
                        position=player_data.get("pos"),
                        is_starter=True,
                        source=self.name,
                    ))

                substitutes = []
                for p in team_lineup.get("substitutes", []):
                    player_data = p.get("player", {})
                    player = PlayerData(
                        id=f"af_{player_data.get('id')}",
                        name=player_data.get("name", ""),
                        position=player_data.get("pos"),
                        source=self.name,
                    )
                    substitutes.append(PlayerMatchPerformanceData(
                        match_id=match_id,
                        player=player,
                        position=player_data.get("pos"),
                        is_starter=False,
                        source=self.name,
                    ))

                lineups[side] = MatchLineupData(
                    match_id=match_id,
                    team=team,
                    formation=formation,
                    starting_xi=starting_xi,
                    substitutes=substitutes,
                    source=self.name,
                )

            return lineups if lineups else None
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing lineups for {match_id}: {e}")
            return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        if not self.enabled:
            return []
        fixture_id = self._extract_fixture_id(match_id)
        if not fixture_id:
            return []

        data = self._get("fixtures/events", {"fixture": fixture_id})
        if not data or not data.get("response"):
            return []

        events = []
        home_team_id = None  # will infer from fixture data

        try:
            for ev in data.get("response", []):
                team_data = ev.get("team", {})
                player_data = ev.get("player", {})
                time_data = ev.get("time", {})
                ev_type = ev.get("type", "")
                detail = ev.get("detail", "")

                # Map event types
                type_map = {
                    "Goal": "GOAL",
                    "Card": ("YELLOW_CARD" if "Yellow" in detail else "RED_CARD"),
                    "subst": "SUBSTITUTION",
                    "Var": None,  # Skip VAR events
                }
                our_type = type_map.get(ev_type)
                if not our_type:
                    if ev_type == "Card":
                        our_type = "YELLOW_CARD" if "Yellow" in detail else "RED_CARD"
                    else:
                        continue

                minute = _safe_int(time_data.get("elapsed"))
                event_id = f"af_{match_id}_{ev.get('time', {}).get('elapsed')}_{our_type}_{player_data.get('id', '')}"

                events.append(MatchEventData(
                    id=event_id,
                    match_id=match_id,
                    type=our_type,
                    minute=minute,
                    player_name=player_data.get("name"),
                    team=TeamData(
                        id=f"af_{team_data.get('id')}",
                        name=team_data.get("name", ""),
                        source=self.name,
                    ),
                    description=detail,
                    source=self.name,
                ))
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing events for {match_id}: {e}")

        return events

    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        """Get injury data for a team from API-Football."""
        if not self.enabled:
            return []
        af_team_id = team_id.replace("af_", "")
        data = self._get("injuries", {"team": af_team_id, "season": datetime.now().year})
        if not data:
            return []
        injuries = []
        for item in data.get("response", []):
            player = item.get("player", {})
            fixture = item.get("fixture", {})
            injuries.append(InjuryData(
                id=f"af_injury_{player.get('id')}",
                player=PlayerData(
                    id=f"af_{player.get('id')}",
                    name=player.get("name", ""),
                    source=self.name,
                ),
                injury_type=item.get("type"),
                status="OUT",
                source=self.name,
            ))
        return injuries

    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        """API-Football doesn't have a dedicated suspensions endpoint."""
        return []

    def _extract_fixture_id(self, match_id: str) -> Optional[int]:
        """Extract integer fixture ID from our composite match ID."""
        try:
            part = match_id.replace("af_", "")
            return int(part)
        except Exception:
            return None

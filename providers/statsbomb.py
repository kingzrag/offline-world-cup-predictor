"""
StatsBomb Open Data Provider

Downloads freely available match data from StatsBomb's public GitHub repository:
  https://github.com/statsbomb/open-data

Data available:
  - competitions.json (list of all available competitions and seasons)
  - matches/{competition_id}/{season_id}.json (match list per competition-season)
  - events/{match_id}.json (detailed event-by-event data including xG, shots, passes, etc.)
  - lineups/{match_id}.json (player lineups per match)
  - three-sixty/{match_id}.json (360 tracking data, where available)

No API key required. All data is MIT-licensed.

NOTE: StatsBomb Open Data covers historical competitions only, not live matches.
Covered competitions include World Cup (men + women), Euro, Copa America, Champions League,
various domestic leagues, and more.
"""

import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests

from providers.base import (
    BaseProvider,
    CompetitionData,
    InjuryData,
    MatchData,
    MatchEventData,
    MatchLineupData,
    MatchStatisticsData,
    PlayerData,
    PlayerMatchPerformanceData,
    StandingData,
    SuspensionData,
    TeamData,
)
from utils.logger import logger

# ---------------------------------------------------------------------------
# StatsBomb Open Data GitHub raw base URL
# ---------------------------------------------------------------------------
_SB_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
_COMPETITIONS_URL = f"{_SB_BASE}/competitions.json"
_MATCHES_URL = f"{_SB_BASE}/matches/{{competition_id}}/{{season_id}}.json"
_EVENTS_URL = f"{_SB_BASE}/events/{{match_id}}.json"
_LINEUPS_URL = f"{_SB_BASE}/lineups/{{match_id}}.json"

_REQUEST_DELAY = 0.5  # seconds between requests

_HEADERS = {
    "User-Agent": "football-prediction-platform/1.0",
    "Accept": "application/json",
}

# Map our competition codes to StatsBomb competition IDs
_COMPETITION_CODE_MAP: Dict[str, int] = {
    "WC": 43,  # FIFA World Cup (men)
    "WWC": 72,  # FIFA World Cup (women)
    "EC": 55,  # UEFA Euro (men)
    "CA": 223,  # Copa América
    "WCQ": 30,  # World Cup Qualifiers
    "CL": 16,  # Champions League
    "PL": 2,  # Premier League
    "AFCON": 6,  # Africa Cup of Nations
}


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except Exception:
        return None


def _safe_int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except Exception:
        return None


def _parse_sb_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return None


class StatsBombProvider(BaseProvider):
    """
    StatsBomb Open Data Provider.

    Downloads match events, lineups, and xG data from the StatsBomb Open Data
    GitHub repository. All data is historical (no live updates).

    Automatically handles:
      - competitions
      - matches
      - events (shots, passes, pressures, carries, tackles, interceptions, xG)
      - lineups
      - defensive actions
    """

    name = "StatsBomb"

    def __init__(self):
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)
        self._competitions_cache: Optional[List[Dict]] = None
        logger.info(f"{self.name} provider initialized (Open Data mode)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_json(self, url: str) -> Optional[Any]:
        """Fetch JSON from a URL, return None on failure."""
        try:
            time.sleep(_REQUEST_DELAY)
            resp = self._session.get(url, timeout=30)
            if resp.status_code == 404:
                logger.debug(f"{self.name}: 404 Not Found: {url}")
                return None
            if resp.status_code != 200:
                logger.warning(f"{self.name}: HTTP {resp.status_code} for {url}")
                return None
            return resp.json()
        except Exception as e:
            logger.warning(f"{self.name}: Request failed for {url}: {e}")
            return None

    def _get_all_competitions(self) -> List[Dict]:
        """Download and cache the StatsBomb competitions list."""
        if self._competitions_cache is not None:
            return self._competitions_cache
        data = self._get_json(_COMPETITIONS_URL)
        if data:
            self._competitions_cache = data
            logger.info(f"{self.name}: Loaded {len(data)} competitions from Open Data")
        else:
            self._competitions_cache = []
        return self._competitions_cache

    def _get_matches_for_season(
        self, competition_id: int, season_id: int
    ) -> List[Dict]:
        """Download match list for a specific competition season."""
        url = _MATCHES_URL.format(competition_id=competition_id, season_id=season_id)
        data = self._get_json(url)
        return data if data else []

    def _get_events(self, match_id: int) -> List[Dict]:
        """Download event-level data for a specific match."""
        url = _EVENTS_URL.format(match_id=match_id)
        data = self._get_json(url)
        return data if data else []

    def _get_lineups(self, match_id: int) -> List[Dict]:
        """Download lineup data for a specific match."""
        url = _LINEUPS_URL.format(match_id=match_id)
        data = self._get_json(url)
        return data if data else []

    # ------------------------------------------------------------------
    # BaseProvider interface
    # ------------------------------------------------------------------

    async def get_competitions(self) -> List[CompetitionData]:
        """Return all available StatsBomb Open Data competitions."""
        raw = self._get_all_competitions()
        competitions = []
        seen = set()
        for comp in raw:
            name = comp.get("competition_name", "")
            cid = comp.get("competition_id")
            key = f"{cid}"
            if key in seen:
                continue
            seen.add(key)
            # Map to our code
            our_code = next(
                (code for code, sb_id in _COMPETITION_CODE_MAP.items() if sb_id == cid),
                f"SB_{cid}",
            )
            competitions.append(
                CompetitionData(
                    id=f"statsbomb_{cid}",
                    name=name,
                    code=our_code,
                    area=comp.get("country_name", "World"),
                    season=str(comp.get("season_name", "")),
                    source=self.name,
                )
            )
        logger.info(f"{self.name}: Found {len(competitions)} unique competitions")
        return competitions

    async def get_competition_standings(
        self, competition_code: str
    ) -> List[StandingData]:
        """StatsBomb Open Data does not include standings."""
        return []

    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        """Get all available matches for a competition code."""
        comp_id = _COMPETITION_CODE_MAP.get(competition_code)
        if not comp_id:
            logger.warning(
                f"{self.name}: No StatsBomb competition ID for code: {competition_code}"
            )
            return []

        # Find all seasons for this competition
        all_comps = self._get_all_competitions()
        seasons = [c for c in all_comps if c.get("competition_id") == comp_id]
        if not seasons:
            logger.warning(
                f"{self.name}: No seasons found for competition {competition_code} (ID: {comp_id})"
            )
            return []

        all_matches = []
        for season in seasons:
            season_id = season.get("season_id")
            season_name = season.get("season_name", "")
            raw_matches = self._get_matches_for_season(comp_id, season_id)
            for m in raw_matches:
                match_data = self._parse_match(m, competition_code, season_name)
                if match_data:
                    all_matches.append(match_data)

        logger.info(
            f"{self.name}: Found {len(all_matches)} matches for {competition_code}"
        )
        return all_matches

    def _parse_match(
        self, m: Dict, competition_code: str, season_name: str
    ) -> Optional[MatchData]:
        """Parse a StatsBomb match dict into our MatchData model."""
        try:
            match_id = m.get("match_id")
            home_team_data = m.get("home_team", {})
            away_team_data = m.get("away_team", {})

            home_team = TeamData(
                id=f"sb_{home_team_data.get('home_team_id')}",
                name=home_team_data.get("home_team_name", ""),
                source=self.name,
            )
            away_team = TeamData(
                id=f"sb_{away_team_data.get('away_team_id')}",
                name=away_team_data.get("away_team_name", ""),
                source=self.name,
            )

            date_str = m.get("match_date", "")
            match_date = _parse_sb_date(date_str)

            home_score = _safe_int(m.get("home_score"))
            away_score = _safe_int(m.get("away_score"))
            status = "FINISHED" if home_score is not None else "SCHEDULED"

            return MatchData(
                id=f"statsbomb_{match_id}",
                competition_id=competition_code,
                home_team=home_team,
                away_team=away_team,
                utc_date=match_date,
                status=status,
                stage=m.get("competition_stage", {}).get("name"),
                home_score=home_score,
                away_score=away_score,
                home_formation=m.get("home_team", {}).get(
                    "home_team_gender"
                ),  # Will fix below
                provider_ids={self.name: str(match_id)},
                source=self.name,
            )
        except Exception as e:
            logger.debug(f"{self.name}: Error parsing match: {e}")
            return None

    async def get_live_matches(self) -> List[MatchData]:
        """StatsBomb Open Data is historical only — no live matches."""
        return []

    async def get_match_statistics(
        self, match_id: str
    ) -> Optional[MatchStatisticsData]:
        """
        Calculate match statistics from StatsBomb event data.
        Aggregates shots, passes, tackles, pressures, xG, and possession from events.
        """
        sb_id = self._extract_sb_id(match_id)
        if not sb_id:
            return None

        events = self._get_events(sb_id)
        if not events:
            return None

        return self._calculate_match_stats_from_events(match_id, events)

    def _extract_sb_id(self, match_id: str) -> Optional[int]:
        """Extract the integer StatsBomb match ID from our composite ID."""
        try:
            part = match_id.replace("statsbomb_", "")
            return int(part)
        except Exception:
            return None

    def _calculate_match_stats_from_events(
        self, match_id: str, events: List[Dict]
    ) -> MatchStatisticsData:
        """Aggregate event-level data into match-level statistics."""
        stats = MatchStatisticsData(match_id=match_id, source=self.name)

        home_team_id = None
        away_team_id = None

        # Identify home/away teams from first event
        for ev in events[:10]:
            period = ev.get("period", 0)
            if period == 1:
                team = ev.get("team", {})
                tid = team.get("id")
                if tid and home_team_id is None:
                    home_team_id = tid
                elif tid and tid != home_team_id and away_team_id is None:
                    away_team_id = tid
                if home_team_id and away_team_id:
                    break

        # Counters
        home_shots = away_shots = 0
        home_sot = away_sot = 0
        home_passes = away_passes = 0
        home_pass_complete = away_pass_complete = 0
        home_tackles = away_tackles = 0
        home_interceptions = away_interceptions = 0
        home_pressures = away_pressures = 0
        home_carries = away_carries = 0
        home_xg = away_xg = 0.0
        home_time = away_time = 0  # in seconds (for possession)

        total_time_seconds = 90 * 60  # approximate

        for ev in events:
            team_id = ev.get("team", {}).get("id")
            is_home = team_id == home_team_id
            etype = ev.get("type", {}).get("name", "")

            if etype == "Shot":
                shot_data = ev.get("shot", {})
                xg = _safe_float(shot_data.get("statsbomb_xg")) or 0.0
                outcome = shot_data.get("outcome", {}).get("name", "")
                on_target = outcome in ("Saved", "Goal", "Saved to Post")
                if is_home:
                    home_shots += 1
                    home_xg += xg
                    if on_target:
                        home_sot += 1
                else:
                    away_shots += 1
                    away_xg += xg
                    if on_target:
                        away_sot += 1

            elif etype == "Pass":
                pass_data = ev.get("pass", {})
                outcome = pass_data.get("outcome", {}).get("name", "")
                complete = (
                    outcome in (None, "") or outcome == "Complete"
                )  # StatsBomb: no outcome = complete
                if is_home:
                    home_passes += 1
                    if complete:
                        home_pass_complete += 1
                else:
                    away_passes += 1
                    if complete:
                        away_pass_complete += 1

            elif etype == "Tackle":
                if is_home:
                    home_tackles += 1
                else:
                    away_tackles += 1

            elif etype == "Interception":
                if is_home:
                    home_interceptions += 1
                else:
                    away_interceptions += 1

            elif etype == "Duel":
                duel_name = (
                    ev.get("duel", {}).get("type", {}).get("name") or ""
                ).lower()
                if "tackle" in duel_name:
                    if is_home:
                        home_tackles += 1
                    else:
                        away_tackles += 1
                if "aerial" in duel_name:
                    if is_home:
                        stats.home_aerial_duels = (stats.home_aerial_duels or 0) + 1
                    else:
                        stats.away_aerial_duels = (stats.away_aerial_duels or 0) + 1

            elif etype == "Pressure":
                if is_home:
                    home_pressures += 1
                else:
                    away_pressures += 1

            elif etype == "Carry":
                duration = _safe_float(ev.get("duration")) or 1.0
                if is_home:
                    home_carries += 1
                    home_time += duration
                else:
                    away_carries += 1
                    away_time += duration

        # Build stats
        stats.home_shots = home_shots
        stats.away_shots = away_shots
        stats.home_shots_on_target = home_sot
        stats.away_shots_on_target = away_sot
        stats.home_expected_goals = round(home_xg, 3)
        stats.away_expected_goals = round(away_xg, 3)
        stats.home_passes = home_passes
        stats.away_passes = away_passes
        stats.home_successful_passes = home_pass_complete
        stats.away_successful_passes = away_pass_complete
        stats.home_tackles = home_tackles
        stats.away_tackles = away_tackles
        stats.home_interceptions = home_interceptions
        stats.away_interceptions = away_interceptions
        stats.home_pressures = home_pressures
        stats.away_pressures = away_pressures
        stats.home_carries = home_carries
        stats.away_carries = away_carries

        if home_passes > 0:
            stats.home_pass_accuracy = round(
                100.0 * home_pass_complete / home_passes, 1
            )
        if away_passes > 0:
            stats.away_pass_accuracy = round(
                100.0 * away_pass_complete / away_passes, 1
            )

        # Possession from carry durations
        total = home_time + away_time
        if total > 0:
            stats.home_possession = round(100.0 * home_time / total, 1)
            stats.away_possession = round(100.0 * away_time / total, 1)

        return stats

    async def get_match_lineups(
        self, match_id: str
    ) -> Optional[Dict[str, MatchLineupData]]:
        """Download and parse lineups from StatsBomb Open Data."""
        sb_id = self._extract_sb_id(match_id)
        if not sb_id:
            return None

        raw = self._get_lineups(sb_id)
        if not raw or len(raw) < 2:
            return None

        try:
            lineups: Dict[str, MatchLineupData] = {}
            for i, team_lineup in enumerate(raw[:2]):
                side = "home" if i == 0 else "away"
                team_name = team_lineup.get("team_name", "")
                team_id = team_lineup.get("team_id")
                players_raw = team_lineup.get("lineup", [])

                starting_xi = []
                substitutes = []
                for p in players_raw:
                    player_name = p.get("player_name", "")
                    player_id = p.get("player_id")
                    position = (
                        p.get("positions", [{}])[0].get("position", "")
                        if p.get("positions")
                        else ""
                    )
                    jersey = p.get("jersey_number")

                    player_data = PlayerData(
                        id=f"sb_{player_id}",
                        name=player_name,
                        position=position,
                        source=self.name,
                    )
                    perf = PlayerMatchPerformanceData(
                        match_id=match_id,
                        player=player_data,
                        position=position,
                        is_starter=True,  # All in lineup are considered starters (StatsBomb includes all)
                        source=self.name,
                    )
                    starting_xi.append(perf)

                team_data = TeamData(
                    id=f"sb_{team_id}",
                    name=team_name,
                    source=self.name,
                )
                lineups[side] = MatchLineupData(
                    match_id=match_id,
                    team=team_data,
                    starting_xi=starting_xi,
                    substitutes=[],
                    source=self.name,
                )

            return lineups
        except Exception as e:
            logger.warning(f"{self.name}: Error parsing lineups for {match_id}: {e}")
            return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        """Parse key events (goals, cards, substitutions) from StatsBomb event stream."""
        sb_id = self._extract_sb_id(match_id)
        if not sb_id:
            return []

        raw_events = self._get_events(sb_id)
        if not raw_events:
            return []

        events = []
        home_team_id = None
        for ev in raw_events[:10]:
            team_id = ev.get("team", {}).get("id")
            if team_id:
                home_team_id = team_id
                break

        KEY_TYPES = {"Shot", "Yellow Card", "Red Card", "Substitution", "Own Goal For"}

        for ev in raw_events:
            etype_name = ev.get("type", {}).get("name", "")
            if etype_name not in KEY_TYPES:
                continue

            try:
                team_id = ev.get("team", {}).get("id")
                is_home = team_id == home_team_id
                minute = ev.get("minute", 0)
                player_name = ev.get("player", {}).get("name", "")

                # Map StatsBomb types to our types
                our_type = {
                    "Shot": "GOAL"
                    if ev.get("shot", {}).get("outcome", {}).get("name") == "Goal"
                    else "SHOT",
                    "Yellow Card": "YELLOW_CARD",
                    "Red Card": "RED_CARD",
                    "Substitution": "SUBSTITUTION",
                    "Own Goal For": "GOAL",
                }.get(etype_name, etype_name.upper().replace(" ", "_"))

                if our_type == "SHOT":
                    continue  # Don't include non-goal shots as events

                event_id = f"sb_{match_id}_{ev.get('id', minute)}_{our_type}"
                events.append(
                    MatchEventData(
                        id=event_id,
                        match_id=match_id,
                        type=our_type,
                        minute=minute,
                        player_name=player_name,
                        is_home=is_home,
                        description=etype_name,
                        source=self.name,
                    )
                )
            except Exception as e:
                logger.debug(f"{self.name}: Error parsing event: {e}")

        return events

    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        """StatsBomb Open Data does not include injury data."""
        return []

    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        """StatsBomb Open Data does not include suspension data."""
        return []

    # ------------------------------------------------------------------
    # StatsBomb-specific: get full event stream for a match
    # ------------------------------------------------------------------

    def get_full_event_stream(self, match_id: str) -> List[Dict]:
        """Get the raw StatsBomb event stream for a match (for advanced analysis)."""
        sb_id = self._extract_sb_id(match_id)
        if not sb_id:
            return []
        return self._get_events(sb_id)

    def get_available_competitions(self) -> List[Dict]:
        """Return the raw StatsBomb competition list."""
        return self._get_all_competitions()

    def get_competition_season_pairs(self, competition_code: str) -> List[Dict]:
        """Return all (competition_id, season_id) pairs for a given competition code."""
        comp_id = _COMPETITION_CODE_MAP.get(competition_code)
        if not comp_id:
            return []
        all_comps = self._get_all_competitions()
        return [c for c in all_comps if c.get("competition_id") == comp_id]

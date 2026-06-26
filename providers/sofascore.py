from typing import Any, Dict, List, Optional

from collectors.sofascore import SofaScoreCollector
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


class SofaScoreProvider(BaseProvider):
    """
    SofaScore Provider
    - Live matches, statistics, lineups, events, player ratings
    - Fails gracefully if blocked by Cloudflare
    """

    name = "SofaScore"

    def __init__(self):
        super().__init__()
        try:
            self.collector = SofaScoreCollector()
            self.enabled = True
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            self.enabled = False

    async def get_competitions(self) -> List[CompetitionData]:
        logger.debug(f"{self.name}: Competition list not implemented")
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
        if not self.enabled:
            logger.warning(f"{self.name} is disabled, skipping live matches")
            return []

        try:
            data = self.collector.get_live_matches()
            if not data or "events" not in data:
                return []

            matches = []
            for event in data.get("events", []):
                try:
                    home_team_data = event.get("homeTeam", {})
                    away_team_data = event.get("awayTeam", {})
                    home_team = TeamData(
                        name=home_team_data.get("name"), source=self.name
                    )
                    away_team = TeamData(
                        name=away_team_data.get("name"), source=self.name
                    )
                    matches.append(
                        MatchData(
                            id=str(event.get("id")),
                            home_team=home_team,
                            away_team=away_team,
                            status=event.get("status"),
                            stage=event.get("tournament", {}).get("name"),
                            provider_ids={self.name: str(event.get("id"))},
                            source=self.name,
                        )
                    )
                except Exception as e:
                    logger.debug(
                        f"{self.name}: Could not parse event {event.get('id')}: {e}"
                    )
                    continue
            return matches
        except Exception as e:
            logger.warning(f"{self.name}: Could not get live matches: {e}")
            return []

    async def get_match_statistics(
        self, match_id: str
    ) -> Optional[MatchStatisticsData]:
        if not self.enabled:
            logger.warning(f"{self.name} is disabled, skipping match statistics")
            return None

        try:
            raw_stats = self.collector.get_match_statistics(match_id)
            if not raw_stats:
                return None

            parsed = self.collector.parse_match_statistics(raw_stats)
            return MatchStatisticsData(
                match_id=match_id,
                home_possession=parsed["home"].get("Ball possession"),
                away_possession=parsed["away"].get("Ball possession"),
                home_shots=parsed["home"].get("Total shots"),
                away_shots=parsed["away"].get("Total shots"),
                home_shots_on_target=parsed["home"].get("Shots on target"),
                away_shots_on_target=parsed["away"].get("Shots on target"),
                home_corners=parsed["home"].get("Corner kicks"),
                away_corners=parsed["away"].get("Corner kicks"),
                home_expected_goals=parsed["home"].get("Expected goals (xG)"),
                away_expected_goals=parsed["away"].get("Expected goals (xG)"),
                home_fouls=parsed["home"].get("Fouls"),
                away_fouls=parsed["away"].get("Fouls"),
                home_offsides=parsed["home"].get("Offsides"),
                away_offsides=parsed["away"].get("Offsides"),
                source=self.name,
            )
        except Exception as e:
            logger.warning(f"{self.name}: Could not get match statistics: {e}")
            return None

    async def get_match_lineups(
        self, match_id: str
    ) -> Optional[Dict[str, MatchLineupData]]:
        if not self.enabled:
            logger.warning(f"{self.name} is disabled, skipping lineups")
            return None

        try:
            raw_lineups = self.collector.get_match_lineups(match_id)
            if not raw_lineups:
                return None

            parsed = self.collector.parse_match_lineups(raw_lineups)
            result = {}
            for side in ["home", "away"]:
                team_data = parsed.get(side, {})
                starting_xi = [
                    PlayerMatchPerformanceData(
                        player=PlayerData(
                            id=str(p.get("sofa_score_player_id")),
                            name=p.get("player_name"),
                            source=self.name,
                        ),
                        position=p.get("position"),
                        is_starter=p.get("is_starter"),
                        rating=p.get("sofa_score_rating"),
                        source=self.name,
                    )
                    for p in team_data.get("players", [])
                    if p.get("is_starter")
                ]
                substitutes = [
                    PlayerMatchPerformanceData(
                        player=PlayerData(
                            id=str(p.get("sofa_score_player_id")),
                            name=p.get("player_name"),
                            source=self.name,
                        ),
                        position=p.get("position"),
                        is_starter=False,
                        rating=p.get("sofa_score_rating"),
                        source=self.name,
                    )
                    for p in team_data.get("players", [])
                    if not p.get("is_starter")
                ]
                result[side] = MatchLineupData(
                    match_id=match_id,
                    formation=team_data.get("formation"),
                    starting_xi=starting_xi,
                    substitutes=substitutes,
                    source=self.name,
                )
            return result
        except Exception as e:
            logger.warning(f"{self.name}: Could not get lineups: {e}")
            return None

    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        if not self.enabled:
            logger.warning(f"{self.name} is disabled, skipping events")
            return []

        try:
            raw_events = self.collector.get_match_events(match_id)
            if not raw_events:
                return []

            parsed = self.collector.parse_match_events(raw_events)
            events = []
            for e in parsed:
                events.append(
                    MatchEventData(
                        id=e.get("sofa_score_id"),
                        match_id=match_id,
                        type=e.get("type"),
                        minute=e.get("minute"),
                        player_name=e.get("player_name"),
                        description=e.get("description"),
                        is_home=e.get("is_home"),
                        source=self.name,
                    )
                )
            return events
        except Exception as e:
            logger.warning(f"{self.name}: Could not get events: {e}")
            return []

    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        logger.debug(f"{self.name}: Team injuries not implemented")
        return []

    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        logger.debug(f"{self.name}: Team suspensions not implemented")
        return []

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
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
)
from providers.football_data import FootballDataProvider
from providers.transfermarkt import TransfermarktProvider
from providers.sofascore import SofaScoreProvider
from providers.fbref import FBrefProvider
from providers.statsbomb import StatsBombProvider
from providers.api_football import APIFootballProvider

# ---------------------------------------------------------------------------
# Simple TTL cache for expensive provider calls
# ---------------------------------------------------------------------------
_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


def _cache_get(key: str) -> Optional[Any]:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(key: str, value: Any):
    _CACHE[key] = (time.time(), value)


async def _with_retry(coro, provider_name: str, max_retries: int = 2, base_delay: float = 1.0):
    """
    Execute an async coroutine with exponential backoff retry on failure.
    Returns None on final failure rather than raising.
    """
    for attempt in range(max_retries + 1):
        try:
            return await coro
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"{provider_name}: Attempt {attempt + 1} failed ({e}), "
                    f"retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"{provider_name}: All {max_retries + 1} attempts failed: {e}")
    return None


class ProviderOrchestrator:
    """
    Orchestrates all data providers to create unified Match Intelligence!
    Merges data from all available providers with fallback logic!
    """
    
    def __init__(self):
        self.providers: List[BaseProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        logger.info("Initializing data providers...")
        
        # Football-Data (always available if API key exists)
        if hasattr(settings, "FOOTBALL_DATA_API_KEY") and settings.FOOTBALL_DATA_API_KEY:
            try:
                fd_provider = FootballDataProvider(settings.FOOTBALL_DATA_API_KEY)
                self.providers.append(fd_provider)
                logger.info(f"Initialized provider: {fd_provider.name}")
            except Exception as e:
                logger.warning(f"Failed to initialize FootballData: {e}")
        
        # Transfermarkt (always available)
        try:
            tm_provider = TransfermarktProvider()
            self.providers.append(tm_provider)
            logger.info(f"Initialized provider: {tm_provider.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Transfermarkt: {e}")
        
        # SofaScore (optional, fails gracefully)
        try:
            ss_provider = SofaScoreProvider()
            self.providers.append(ss_provider)
            logger.info(f"Initialized provider: {ss_provider.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize SofaScore: {e}")
        
        # FBref (optional, skeleton)
        try:
            fb_provider = FBrefProvider()
            self.providers.append(fb_provider)
            logger.info(f"Initialized provider: {fb_provider.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize FBref: {e}")
        
        # StatsBomb (optional, skeleton)
        try:
            sb_provider = StatsBombProvider()
            self.providers.append(sb_provider)
            logger.info(f"Initialized provider: {sb_provider.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize StatsBomb: {e}")
        
        # API-Football (optional, only if API key exists)
        try:
            af_provider = APIFootballProvider()
            if af_provider.enabled:
                self.providers.append(af_provider)
                logger.info(f"Initialized provider: {af_provider.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize APIFootball: {e}")
        
        logger.info(f"Total providers initialized: {len(self.providers)}")
    
    def get_provider_by_name(self, name: str) -> Optional[BaseProvider]:
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None
    
    async def get_merged_competitions(self) -> List[CompetitionData]:
        cache_key = "merged_competitions"
        cached = _cache_get(cache_key)
        if cached:
            logger.debug("Returning cached competitions")
            return cached

        all_competitions = []
        seen_codes = set()
        
        for provider in self.providers:
            try:
                competitions = await _with_retry(
                    provider.get_competitions(), provider.name
                ) or []
                for comp in competitions:
                    if comp.code and comp.code not in seen_codes:
                        seen_codes.add(comp.code)
                        all_competitions.append(comp)
            except Exception as e:
                logger.warning(f"Error getting competitions from {provider.name}: {e}")
        
        _cache_set(cache_key, all_competitions)
        return all_competitions
    
    async def get_merged_live_matches(self) -> List[MatchData]:
        """Get live matches from all providers, merge by team names"""
        matches_by_key = {}
        
        for provider in self.providers:
            try:
                matches = await provider.get_live_matches()
                for match in matches:
                    # Create a unique key based on team names
                    if match.home_team and match.away_team:
                        key = tuple(sorted([match.home_team.name, match.away_team.name]))
                        if key not in matches_by_key:
                            matches_by_key[key] = match
                        else:
                            # Merge missing fields from this provider
                            matches_by_key[key] = self._merge_match_data(matches_by_key[key], match)
            except Exception as e:
                logger.warning(f"Error getting live matches from {provider.name}: {e}")
        
        return list(matches_by_key.values())
    
    async def get_merged_competition_matches(self, competition_code: str) -> List[MatchData]:
        matches_by_id = {}
        
        for provider in self.providers:
            try:
                matches = await provider.get_competition_matches(competition_code)
                for match in matches:
                    if match.id and match.id not in matches_by_id:
                        matches_by_id[match.id] = match
                    elif match.id:
                        matches_by_id[match.id] = self._merge_match_data(matches_by_id[match.id], match)
            except Exception as e:
                logger.warning(f"Error getting matches from {provider.name}: {e}")
        
        return list(matches_by_id.values())
    
    async def get_merged_match_statistics(self, match_id: str, provider_hints: Optional[Dict[str, str]] = None) -> Optional[MatchStatisticsData]:
        for provider in self.providers:
            try:
                stats = await provider.get_match_statistics(match_id)
                if stats:
                    logger.info(f"Got match stats from {provider.name}")
                    return stats
            except Exception as e:
                logger.debug(f"Could not get stats from {provider.name}: {e}")
        
        # If we have provider hints, try those
        if provider_hints:
            for provider_name, provider_match_id in provider_hints.items():
                provider = self.get_provider_by_name(provider_name)
                if provider:
                    try:
                        stats = await provider.get_match_statistics(provider_match_id)
                        if stats:
                            logger.info(f"Got match stats from {provider.name} using hint")
                            return stats
                    except Exception as e:
                        logger.debug(f"Could not get stats from {provider.name}: {e}")
        
        return None
    
    async def get_merged_match_lineups(self, match_id: str, provider_hints: Optional[Dict[str, str]] = None) -> Optional[Dict[str, MatchLineupData]]:
        for provider in self.providers:
            try:
                lineups = await provider.get_match_lineups(match_id)
                if lineups:
                    logger.info(f"Got match lineups from {provider.name}")
                    return lineups
            except Exception as e:
                logger.debug(f"Could not get lineups from {provider.name}: {e}")
        
        if provider_hints:
            for provider_name, provider_match_id in provider_hints.items():
                provider = self.get_provider_by_name(provider_name)
                if provider:
                    try:
                        lineups = await provider.get_match_lineups(provider_match_id)
                        if lineups:
                            logger.info(f"Got lineups from {provider.name} using hint")
                            return lineups
                    except Exception as e:
                        logger.debug(f"Could not get lineups from {provider.name}: {e}")
        
        return None
    
    async def get_merged_match_events(self, match_id: str, provider_hints: Optional[Dict[str, str]] = None) -> List[MatchEventData]:
        all_events = []
        seen_event_ids = set()
        
        for provider in self.providers:
            try:
                events = await provider.get_match_events(match_id)
                for event in events:
                    if event.id and event.id not in seen_event_ids:
                        seen_event_ids.add(event.id)
                        all_events.append(event)
            except Exception as e:
                logger.debug(f"Could not get events from {provider.name}: {e}")
        
        if provider_hints:
            for provider_name, provider_match_id in provider_hints.items():
                provider = self.get_provider_by_name(provider_name)
                if provider:
                    try:
                        events = await provider.get_match_events(provider_match_id)
                        for event in events:
                            if event.id and event.id not in seen_event_ids:
                                seen_event_ids.add(event.id)
                                all_events.append(event)
                    except Exception as e:
                        logger.debug(f"Could not get events from {provider.name}: {e}")
        
        return all_events
    
    async def get_merged_team_injuries(self, team_name: str) -> List[InjuryData]:
        all_injuries = []
        seen_players = set()
        
        for provider in self.providers:
            try:
                injuries = await provider.get_team_injuries(team_name)
                for injury in injuries:
                    if injury.player and injury.player.name and injury.player.name not in seen_players:
                        seen_players.add(injury.player.name)
                        all_injuries.append(injury)
            except Exception as e:
                logger.debug(f"Could not get injuries from {provider.name}: {e}")
        
        return all_injuries
    
    async def get_merged_team_suspensions(self, team_name: str) -> List[SuspensionData]:
        all_suspensions = []
        seen_players = set()
        
        for provider in self.providers:
            try:
                suspensions = await provider.get_team_suspensions(team_name)
                for suspension in suspensions:
                    if suspension.player and suspension.player.name and suspension.player.name not in seen_players:
                        seen_players.add(suspension.player.name)
                        all_suspensions.append(suspension)
            except Exception as e:
                logger.debug(f"Could not get suspensions from {provider.name}: {e}")
        
        return all_suspensions
    
    def _merge_match_data(self, existing: MatchData, new: MatchData) -> MatchData:
        """Merge two MatchData objects, prioritizing existing fields"""
        merged = MatchData(
            id=existing.id or new.id,
            competition_id=existing.competition_id or new.competition_id,
            home_team=existing.home_team or new.home_team,
            away_team=existing.away_team or new.away_team,
            utc_date=existing.utc_date or new.utc_date,
            status=existing.status or new.status,
            stage=existing.stage or new.stage,
            group=existing.group or new.group,
            home_score=existing.home_score or new.home_score,
            away_score=existing.away_score or new.away_score,
            winner=existing.winner or new.winner,
            live_minute=existing.live_minute or new.live_minute,
            current_home_score=existing.current_home_score or new.current_home_score,
            current_away_score=existing.current_away_score or new.current_away_score,
            home_possession=existing.home_possession or new.home_possession,
            away_possession=existing.away_possession or new.away_possession,
            home_expected_goals=existing.home_expected_goals or new.home_expected_goals,
            away_expected_goals=existing.away_expected_goals or new.away_expected_goals,
            home_formation=existing.home_formation or new.home_formation,
            away_formation=existing.away_formation or new.away_formation,
            home_red_cards=existing.home_red_cards or new.home_red_cards,
            away_red_cards=existing.away_red_cards or new.away_red_cards,
            home_yellow_cards=existing.home_yellow_cards or new.home_yellow_cards,
            away_yellow_cards=existing.away_yellow_cards or new.away_yellow_cards,
            source=f"{existing.source},{new.source}" if existing.source and new.source else existing.source or new.source,
            provider_ids={}
        )
        
        # Merge provider IDs
        if existing.provider_ids:
            merged.provider_ids.update(existing.provider_ids)
        if new.provider_ids:
            merged.provider_ids.update(new.provider_ids)
        
        return merged

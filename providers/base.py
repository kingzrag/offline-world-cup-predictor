from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from utils.logger import logger


# --- Unified Data Models ---
@dataclass
class TeamData:
    """Unified representation of a team (national or club)"""

    id: Optional[str] = None
    name: Optional[str] = None
    short_name: Optional[str] = None
    tla: Optional[str] = None
    crest_url: Optional[str] = None
    market_value: Optional[float] = None
    fifa_rank: Optional[int] = None
    elo_rank: Optional[int] = None
    source: Optional[str] = None


@dataclass
class PlayerData:
    """Unified representation of a player"""

    id: Optional[str] = None
    name: Optional[str] = None
    position: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    nationality: Optional[str] = None
    market_value: Optional[float] = None
    source: Optional[str] = None


@dataclass
class MatchData:
    """Unified representation of a football match"""

    id: Optional[str] = None
    competition_id: Optional[str] = None
    home_team: Optional[TeamData] = None
    away_team: Optional[TeamData] = None
    utc_date: Optional[datetime] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    group: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    winner: Optional[str] = None
    live_minute: Optional[int] = None
    current_home_score: Optional[int] = None
    current_away_score: Optional[int] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_expected_goals: Optional[float] = None
    away_expected_goals: Optional[float] = None
    home_formation: Optional[str] = None
    away_formation: Optional[str] = None
    home_red_cards: Optional[int] = None
    away_red_cards: Optional[int] = None
    home_yellow_cards: Optional[int] = None
    away_yellow_cards: Optional[int] = None
    source: Optional[str] = None
    provider_ids: Optional[Dict[str, str]] = (
        None  # Maps provider name to their match ID
    )


@dataclass
class CompetitionData:
    """Unified representation of a football competition"""

    id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    area: Optional[str] = None
    season: Optional[str] = None
    source: Optional[str] = None


@dataclass
class StandingData:
    """Unified representation of a competition standing row"""

    competition_id: Optional[str] = None
    team: Optional[TeamData] = None
    position: Optional[int] = None
    played_games: Optional[int] = None
    won: Optional[int] = None
    draw: Optional[int] = None
    lost: Optional[int] = None
    points: Optional[int] = None
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None
    goals_difference: Optional[int] = None
    source: Optional[str] = None


@dataclass
class MatchStatisticsData:
    """Unified representation of match statistics"""

    match_id: Optional[str] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_expected_goals: Optional[float] = None
    away_expected_goals: Optional[float] = None
    home_fouls: Optional[int] = None
    away_fouls: Optional[int] = None
    home_offsides: Optional[int] = None
    away_offsides: Optional[int] = None
    home_passes: Optional[int] = None
    away_passes: Optional[int] = None
    home_successful_passes: Optional[int] = None
    away_successful_passes: Optional[int] = None
    home_pass_accuracy: Optional[float] = None
    away_pass_accuracy: Optional[float] = None
    home_tackles: Optional[int] = None
    away_tackles: Optional[int] = None
    home_interceptions: Optional[int] = None
    away_interceptions: Optional[int] = None
    home_aerial_duels: Optional[int] = None
    away_aerial_duels: Optional[int] = None
    home_pressures: Optional[int] = None
    away_pressures: Optional[int] = None
    home_carries: Optional[int] = None
    away_carries: Optional[int] = None
    source: Optional[str] = None


@dataclass
class PlayerMatchPerformanceData:
    """Unified representation of a player's performance in a match"""

    match_id: Optional[str] = None
    player: Optional[PlayerData] = None
    team: Optional[TeamData] = None
    position: Optional[str] = None
    is_starter: Optional[bool] = None
    rating: Optional[float] = None
    minutes_played: Optional[int] = None
    goals: Optional[int] = None
    assists: Optional[int] = None
    shots: Optional[int] = None
    shots_on_target: Optional[int] = None
    passes: Optional[int] = None
    successful_passes: Optional[int] = None
    pass_accuracy: Optional[float] = None
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    saves: Optional[int] = None
    yellow_cards: Optional[int] = None
    red_cards: Optional[int] = None
    aerial_duels: Optional[int] = None
    aerial_duels_won: Optional[int] = None
    key_passes: Optional[int] = None
    pressures: Optional[int] = None
    carries: Optional[int] = None
    statsbomb_xg: Optional[float] = None
    source: Optional[str] = None


@dataclass
class MatchLineupData:
    """Unified representation of a match lineup"""

    match_id: Optional[str] = None
    team: Optional[TeamData] = None
    formation: Optional[str] = None
    starting_xi: Optional[List[PlayerMatchPerformanceData]] = None
    substitutes: Optional[List[PlayerMatchPerformanceData]] = None
    source: Optional[str] = None


@dataclass
class MatchEventData:
    """Unified representation of a match event (goal, card, substitution, etc.)"""

    id: Optional[str] = None
    match_id: Optional[str] = None
    type: Optional[str] = None  # GOAL, YELLOW_CARD, RED_CARD, SUBSTITUTION, etc.
    minute: Optional[int] = None
    description: Optional[str] = None
    player_name: Optional[str] = None
    team: Optional[TeamData] = None
    is_home: Optional[bool] = None
    source: Optional[str] = None


@dataclass
class InjuryData:
    """Unified representation of a player injury"""

    id: Optional[str] = None
    player: Optional[PlayerData] = None
    team: Optional[TeamData] = None
    injury_type: Optional[str] = None
    status: Optional[str] = None  # OUT, DOUBTFUL, FIT
    return_date: Optional[datetime] = None
    source: Optional[str] = None


@dataclass
class SuspensionData:
    """Unified representation of a player suspension"""

    id: Optional[str] = None
    player: Optional[PlayerData] = None
    team: Optional[TeamData] = None
    reason: Optional[str] = None
    status: Optional[str] = None  # PENDING, SERVING, SERVED
    matches_missed: Optional[int] = None
    source: Optional[str] = None


# --- Base Provider Class ---
class BaseProvider(ABC):
    """
    Abstract base class for all football data providers.
    All providers must implement these methods, but can raise NotImplementedError
    for functionality they don't support.
    """

    name: str = "BaseProvider"
    enabled: bool = True

    def __init__(self):
        logger.info(f"Initialized provider: {self.name}")

    @abstractmethod
    async def get_competitions(self) -> List[CompetitionData]:
        """Get list of competitions supported by this provider"""
        raise NotImplementedError

    @abstractmethod
    async def get_competition_standings(
        self, competition_code: str
    ) -> List[StandingData]:
        """Get standings for a specific competition"""
        raise NotImplementedError

    @abstractmethod
    async def get_competition_matches(self, competition_code: str) -> List[MatchData]:
        """Get matches for a specific competition"""
        raise NotImplementedError

    @abstractmethod
    async def get_live_matches(self) -> List[MatchData]:
        """Get currently live matches"""
        raise NotImplementedError

    @abstractmethod
    async def get_match_statistics(
        self, match_id: str
    ) -> Optional[MatchStatisticsData]:
        """Get detailed statistics for a specific match"""
        raise NotImplementedError

    @abstractmethod
    async def get_match_lineups(
        self, match_id: str
    ) -> Optional[Dict[str, MatchLineupData]]:
        """Get lineups for a specific match (home and away)"""
        raise NotImplementedError

    @abstractmethod
    async def get_match_events(self, match_id: str) -> List[MatchEventData]:
        """Get events for a specific match"""
        raise NotImplementedError

    @abstractmethod
    async def get_team_injuries(self, team_id: str) -> List[InjuryData]:
        """Get injured players for a specific team"""
        raise NotImplementedError

    @abstractmethod
    async def get_team_suspensions(self, team_id: str) -> List[SuspensionData]:
        """Get suspended players for a specific team"""
        raise NotImplementedError


# --- Match Intelligence Model ---
@dataclass
class MatchIntelligence:
    """
    Comprehensive intelligence scores for a match (home vs away).
    All scores are computed from available provider data.
    Scores are floating-point values; interpretation varies by metric.
    """

    match_id: Optional[int] = None

    # --- Attacking / Defensive ---
    home_attacking_strength: float = 0.0
    away_attacking_strength: float = 0.0
    home_defensive_strength: float = 0.0
    away_defensive_strength: float = 0.0

    # --- Midfield & Passing ---
    home_midfield_control: float = 0.0
    away_midfield_control: float = 0.0
    home_passing_dominance: float = 0.0
    away_passing_dominance: float = 0.0

    # --- Goalkeeper ---
    home_goalkeeper_performance: float = 0.0
    away_goalkeeper_performance: float = 0.0

    # --- Pressing ---
    home_pressing_intensity: float = 0.0
    away_pressing_intensity: float = 0.0

    # --- Set Pieces ---
    home_set_piece_threat: float = 0.0
    away_set_piece_threat: float = 0.0

    # --- Discipline ---
    home_discipline_score: float = 0.0
    away_discipline_score: float = 0.0

    # --- Fatigue ---
    home_fatigue_score: float = 0.0
    away_fatigue_score: float = 0.0

    # --- Substitutions ---
    home_substitution_impact: float = 0.0
    away_substitution_impact: float = 0.0

    # --- Squad Availability ---
    home_player_availability_score: float = 1.0
    away_player_availability_score: float = 1.0
    home_injury_impact: float = 0.0
    away_injury_impact: float = 0.0
    home_suspension_impact: float = 0.0
    away_suspension_impact: float = 0.0

    # --- Formation & Momentum ---
    home_formation_stability: float = 0.0
    away_formation_stability: float = 0.0
    home_momentum_score: float = 0.0
    away_momentum_score: float = 0.0

    # --- Composite confidence ---
    confidence_score: float = 0.0

    # --- Metadata ---
    data_completeness: float = 0.0  # 0.0–1.0 fraction of metrics successfully computed
    sources_used: Optional[List[str]] = None
    computed_at: Optional[datetime] = None

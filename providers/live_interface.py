"""
providers/live_interface.py
===========================
Abstract Live Football Provider Interface.

This interface defines the contract that any live score provider must implement.
It enforces separation between pre-match model features and live in-play data.

PRE-MATCH MODEL DATA must NEVER be contaminated with live/post-match data.
The existing 29 international features and 26 domestic-club features must remain
unchanged. Live data flows separately into the live prediction adjustment engine.

Verified live capabilities:
  - API-Football: SUSPENDED (account error as of 2026-09-08)
  - Football-Data.org: DELAYED only, NOT real-time
  - TheSportsDB free: NOT real-time (Premium = 2-min updates)
  
A future provider with genuine real-time capability can implement this interface
without touching model_service.py or feature definitions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class LiveProviderStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    DEGRADED = "DEGRADED"


class LiveEventType(str, Enum):
    GOAL = "GOAL"
    YELLOW_CARD = "YELLOW_CARD"
    RED_CARD = "RED_CARD"
    SUBSTITUTION = "SUBSTITUTION"
    PENALTY = "PENALTY"
    VAR = "VAR"
    KICKOFF = "KICKOFF"
    HALFTIME = "HALFTIME"
    FULLTIME = "FULLTIME"
    OWN_GOAL = "OWN_GOAL"
    PENALTY_MISS = "PENALTY_MISS"


@dataclass
class LiveEvent:
    """A single in-play event."""
    event_id: str
    match_id: str
    minute: Optional[int]
    added_time: Optional[int]
    team_id: Optional[str]
    player_id: Optional[str]
    player_name: Optional[str]
    event_type: LiveEventType
    event_detail: Optional[str]
    source: str
    occurred_at: Optional[datetime] = None


@dataclass
class LiveMatchStatistics:
    """Live in-play statistics snapshot."""
    match_id: str
    minute: int
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_fouls: Optional[int] = None
    away_fouls: Optional[int] = None
    source: str = ""
    retrieved_at: Optional[datetime] = None


@dataclass
class LiveMatch:
    """
    Current live state of an in-progress match.
    
    This is SEPARATE from pre-match model features. Never allow fields here
    to leak into the XGBoost/Dixon-Coles pre-match feature vectors.
    """
    match_id: str
    status: str           # IN_PLAY, PAUSED, HALFTIME, FULLTIME
    minute: Optional[int]
    home_score: int
    away_score: int
    home_team_id: Optional[str]
    away_team_id: Optional[str]
    home_red_cards: int = 0
    away_red_cards: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    events: List[LiveEvent] = field(default_factory=list)
    statistics: Optional[LiveMatchStatistics] = None
    last_updated: Optional[datetime] = None
    source: str = ""


class LiveFootballProvider(ABC):
    """
    Abstract interface for live football data providers.
    
    All live data must go through this interface to ensure:
    1. Clean separation from pre-match model features
    2. Consistent error handling and circuit-breaker behavior
    3. Proper source tracking
    """

    name: str = "AbstractLiveProvider"
    provider_status: LiveProviderStatus = LiveProviderStatus.UNAVAILABLE
    
    # Circuit breaker state
    _consecutive_failures: int = 0
    _circuit_breaker_threshold: int = 5
    _circuit_open: bool = False
    _last_success: Optional[datetime] = None

    def is_operational(self) -> bool:
        """Returns True only if provider is genuinely providing live data."""
        return (
            self.provider_status == LiveProviderStatus.ACTIVE
            and not self._circuit_open
        )

    def record_failure(self):
        """Record a consecutive failure; open circuit if threshold exceeded."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._circuit_breaker_threshold:
            self._circuit_open = True
            self.provider_status = LiveProviderStatus.DEGRADED

    def record_success(self):
        """Record a success; reset circuit breaker."""
        self._consecutive_failures = 0
        self._circuit_open = False
        self._last_success = datetime.utcnow()

    @abstractmethod
    def get_live_matches(self) -> List[LiveMatch]:
        """
        Return all currently in-play matches.
        Must return [] if provider is unavailable rather than raising.
        """
        ...

    @abstractmethod
    def get_match_status(self, match_id: str) -> Optional[str]:
        """Return current status string for a match."""
        ...

    @abstractmethod
    def get_match_score(self, match_id: str) -> Optional[Dict[str, int]]:
        """Return {'home': int, 'away': int} or None."""
        ...

    @abstractmethod
    def get_match_events(self, match_id: str) -> List[LiveEvent]:
        """Return list of in-play events for a match."""
        ...

    @abstractmethod
    def get_match_statistics(self, match_id: str) -> Optional[LiveMatchStatistics]:
        """Return live statistics snapshot."""
        ...

    @abstractmethod
    def get_match_lineups(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Return lineups if available from live provider."""
        ...


class NullLiveProvider(LiveFootballProvider):
    """
    No-op live provider used when no real live source is available.
    All methods return safe empty values. Never crashes the prediction stack.
    """

    name = "NullLiveProvider"
    provider_status = LiveProviderStatus.UNAVAILABLE

    def get_live_matches(self) -> List[LiveMatch]:
        return []

    def get_match_status(self, match_id: str) -> Optional[str]:
        return None

    def get_match_score(self, match_id: str) -> Optional[Dict[str, int]]:
        return None

    def get_match_events(self, match_id: str) -> List[LiveEvent]:
        return []

    def get_match_statistics(self, match_id: str) -> Optional[LiveMatchStatistics]:
        return None

    def get_match_lineups(self, match_id: str) -> Optional[Dict[str, Any]]:
        return None


# Singleton: returns NullLiveProvider until a working live source is verified
_live_provider: LiveFootballProvider = NullLiveProvider()


def get_live_provider() -> LiveFootballProvider:
    """Return the current active live provider (or NullLiveProvider if none)."""
    return _live_provider


def register_live_provider(provider: LiveFootballProvider) -> None:
    """Register a new live provider if it is operational."""
    global _live_provider
    if provider.is_operational():
        _live_provider = provider
        import logging
        logging.getLogger(__name__).info(
            f"Registered live provider: {provider.name}"
        )
    else:
        import logging
        logging.getLogger(__name__).warning(
            f"Provider {provider.name} is not operational; keeping {_live_provider.name}"
        )

from providers.base import (
    # Canonical interface — all services should type-hint against this
    FootballProvider,
    # Backward-compat alias
    BaseProvider,
    # Unified data models
    CompetitionData,
    MatchData,
    TeamData,
    PlayerData,
    StandingData,
    MatchStatisticsData,
    MatchLineupData,
    MatchEventData,
    PlayerMatchPerformanceData,
    InjuryData,
    SuspensionData,
    MatchIntelligence,
)

# Concrete provider implementations
from providers.football_data import FootballDataProvider
from providers.api_football import APIFootballProvider
from providers.sportmonks import SportMonksProvider

# Ancillary / enrichment providers (not part of the FootballProvider interface)
from providers.transfermarkt import TransfermarktProvider
from providers.sofascore import SofaScoreProvider
from providers.fbref import FBrefProvider
from providers.statsbomb import StatsBombProvider

# Multi-provider orchestrator (legacy enrichment path)
from providers.orchestrator import ProviderOrchestrator

# Factory — resolves providers by name, use this in services
from providers.factory import ProviderFactory


__all__ = [
    # Interface
    "FootballProvider",
    "BaseProvider",
    # Data models
    "CompetitionData",
    "MatchData",
    "TeamData",
    "PlayerData",
    "StandingData",
    "MatchStatisticsData",
    "MatchLineupData",
    "MatchEventData",
    "PlayerMatchPerformanceData",
    "InjuryData",
    "SuspensionData",
    "MatchIntelligence",
    # Concrete fixture/match providers
    "FootballDataProvider",
    "ApiFootballProvider",
    "SportMonksProvider",
    # Enrichment providers
    "TransfermarktProvider",
    "SofaScoreProvider",
    "FBrefProvider",
    "StatsBombProvider",
    # Factory & orchestrator
    "ProviderFactory",
    "ProviderOrchestrator",
]

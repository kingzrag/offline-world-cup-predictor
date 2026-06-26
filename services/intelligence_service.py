"""
IntelligenceService — Unified Match Intelligence Calculator

Computes 16 intelligence metrics for any match using all available
provider data stored in the database:

  1.  attacking_strength       — shots + xG from recent matches
  2.  defensive_strength       — goals conceded + clean sheet rate
  3.  midfield_control         — pass accuracy + possession differential
  4.  goalkeeper_performance   — saves per match
  5.  passing_dominance        — total passes + accuracy
  6.  pressing_intensity       — tackles + interceptions per match
  7.  set_piece_threat         — corners per match
  8.  discipline_score         — inverse of cards per match
  9.  fatigue_score            — days since last match (more = worse)
  10. substitution_impact      — avg rating of substitutes vs starters
  11. player_availability_score — (squad - injured - suspended) / squad
  12. injury_impact            — market value of missing players
  13. suspension_impact        — number of suspended key players
  14. formation_stability      — same formation used in recent matches
  15. momentum_score           — weighted recent results
  16. confidence_score         — composite weighted average

All metrics use safe defaults when data is missing.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from models import (
    Injury,
    Match,
    MatchEvent,
    MatchLineup,
    MatchStatistic,
    NationalTeamPlayer,
    PlayerMatchPerformance,
    Suspension,
    Team,
)
from providers.base import MatchIntelligence
from utils.logger import logger

_SQUAD_SIZE = 23  # typical national team squad size
_RECENT_MATCHES = 5  # number of recent matches for form calculations
_FORM_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]  # most recent = highest weight


class IntelligenceService:
    """
    Unified Match Intelligence computation service.

    Generates all intelligence features from data stored in the database
    (populated by the data collection pipeline).
    """

    def __init__(self):
        pass

    def calculate_match_intelligence(
        self, db: Session, match: Match
    ) -> MatchIntelligence:
        """
        Calculate all 16 intelligence features for a given match.
        Returns a MatchIntelligence dataclass populated from DB data.
        """
        logger.info(
            f"Calculating intelligence for match {match.id}: "
            f"{getattr(match.home_team, 'name', '?')} vs "
            f"{getattr(match.away_team, 'name', '?')}"
        )

        intelligence = MatchIntelligence(
            match_id=match.id,
            sources_used=[],
            computed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        metrics_computed = 0
        total_metrics = 16

        try:
            # 1. Attacking Strength
            home_atk, away_atk = self._calc_attacking_strength(db, match)
            intelligence.home_attacking_strength = home_atk
            intelligence.away_attacking_strength = away_atk
            if home_atk > 0 or away_atk > 0:
                metrics_computed += 1

            # 2. Defensive Strength
            home_def, away_def = self._calc_defensive_strength(db, match)
            intelligence.home_defensive_strength = home_def
            intelligence.away_defensive_strength = away_def
            if home_def > 0 or away_def > 0:
                metrics_computed += 1

            # 3. Midfield Control
            home_mid, away_mid = self._calc_midfield_control(db, match)
            intelligence.home_midfield_control = home_mid
            intelligence.away_midfield_control = away_mid
            if home_mid > 0 or away_mid > 0:
                metrics_computed += 1

            # 4. Goalkeeper Performance
            home_gk, away_gk = self._calc_goalkeeper_performance(db, match)
            intelligence.home_goalkeeper_performance = home_gk
            intelligence.away_goalkeeper_performance = away_gk
            if home_gk > 0 or away_gk > 0:
                metrics_computed += 1

            # 5. Passing Dominance
            home_pass, away_pass = self._calc_passing_dominance(db, match)
            intelligence.home_passing_dominance = home_pass
            intelligence.away_passing_dominance = away_pass
            if home_pass > 0 or away_pass > 0:
                metrics_computed += 1

            # 6. Pressing Intensity
            home_press, away_press = self._calc_pressing_intensity(db, match)
            intelligence.home_pressing_intensity = home_press
            intelligence.away_pressing_intensity = away_press
            if home_press > 0 or away_press > 0:
                metrics_computed += 1

            # 7. Set-Piece Threat
            home_sp, away_sp = self._calc_set_piece_threat(db, match)
            intelligence.home_set_piece_threat = home_sp
            intelligence.away_set_piece_threat = away_sp
            if home_sp > 0 or away_sp > 0:
                metrics_computed += 1

            # 8. Discipline Score
            home_disc, away_disc = self._calc_discipline_score(db, match)
            intelligence.home_discipline_score = home_disc
            intelligence.away_discipline_score = away_disc
            if home_disc > 0 or away_disc > 0:
                metrics_computed += 1

            # 9. Fatigue Score
            home_fat, away_fat = self._calc_fatigue_score(db, match)
            intelligence.home_fatigue_score = home_fat
            intelligence.away_fatigue_score = away_fat
            if home_fat >= 0 or away_fat >= 0:
                metrics_computed += 1

            # 10. Substitution Impact
            home_sub, away_sub = self._calc_substitution_impact(db, match)
            intelligence.home_substitution_impact = home_sub
            intelligence.away_substitution_impact = away_sub
            if home_sub != 0 or away_sub != 0:
                metrics_computed += 1

            # 11 + 12 + 13. Player Availability, Injury Impact, Suspension Impact
            home_avail, away_avail = self._calc_player_availability(db, match)
            intelligence.home_player_availability_score = home_avail
            intelligence.away_player_availability_score = away_avail
            metrics_computed += 1

            home_inj, away_inj = self._calc_injury_impact(db, match)
            intelligence.home_injury_impact = home_inj
            intelligence.away_injury_impact = away_inj
            if home_inj > 0 or away_inj > 0:
                metrics_computed += 1

            home_susp, away_susp = self._calc_suspension_impact(db, match)
            intelligence.home_suspension_impact = home_susp
            intelligence.away_suspension_impact = away_susp
            metrics_computed += 1

            # 14. Formation Stability
            home_form_stab, away_form_stab = self._calc_formation_stability(db, match)
            intelligence.home_formation_stability = home_form_stab
            intelligence.away_formation_stability = away_form_stab
            if home_form_stab > 0 or away_form_stab > 0:
                metrics_computed += 1

            # 15. Momentum Score
            home_mom, away_mom = self._calc_momentum_score(db, match)
            intelligence.home_momentum_score = home_mom
            intelligence.away_momentum_score = away_mom
            if home_mom != 0 or away_mom != 0:
                metrics_computed += 1

            # Additional engineered ML-only features (backward-compatible extension)
            home_engineered = self._build_team_engineered_metrics(
                db, match, match.home_team_id
            )
            away_engineered = self._build_team_engineered_metrics(
                db, match, match.away_team_id
            )
            intelligence.home_goalkeeper_strength = home_engineered[
                "goalkeeper_strength"
            ]
            intelligence.away_goalkeeper_strength = away_engineered[
                "goalkeeper_strength"
            ]
            intelligence.home_passing_strength = home_engineered["passing_strength"]
            intelligence.away_passing_strength = away_engineered["passing_strength"]
            intelligence.home_recent_form = home_engineered["recent_form"]
            intelligence.away_recent_form = away_engineered["recent_form"]
            intelligence.home_aerial_dominance = home_engineered["aerial_dominance"]
            intelligence.away_aerial_dominance = away_engineered["aerial_dominance"]
            intelligence.home_pressing_strength = home_engineered["pressing_strength"]
            intelligence.away_pressing_strength = away_engineered["pressing_strength"]
            intelligence.home_defensive_stability = home_engineered[
                "defensive_stability"
            ]
            intelligence.away_defensive_stability = away_engineered[
                "defensive_stability"
            ]
            intelligence.home_attacking_efficiency = home_engineered[
                "attacking_efficiency"
            ]
            intelligence.away_attacking_efficiency = away_engineered[
                "attacking_efficiency"
            ]
            intelligence.home_finishing_quality = home_engineered["finishing_quality"]
            intelligence.away_finishing_quality = away_engineered["finishing_quality"]
            intelligence.home_set_piece_strength = home_engineered["set_piece_strength"]
            intelligence.away_set_piece_strength = away_engineered["set_piece_strength"]
            intelligence.home_squad_availability = home_engineered["squad_availability"]
            intelligence.away_squad_availability = away_engineered["squad_availability"]
            intelligence.home_tactical_stability = home_engineered["tactical_stability"]
            intelligence.away_tactical_stability = away_engineered["tactical_stability"]

            # 16. Confidence Score (composite)
            intelligence.confidence_score = self._calc_confidence_score(intelligence)
            metrics_computed += 1

            # Metadata
            intelligence.data_completeness = round(metrics_computed / total_metrics, 3)
            intelligence.sources_used = self._detect_sources(db, match)

        except Exception as e:
            logger.error(
                f"Error computing intelligence for match {match.id}: {e}", exc_info=True
            )

        logger.info(
            f"Intelligence computed for match {match.id}: "
            f"{metrics_computed}/{total_metrics} metrics, "
            f"completeness={intelligence.data_completeness:.0%}, "
            f"confidence={intelligence.confidence_score:.2f}"
        )
        return intelligence

    # ------------------------------------------------------------------
    # Individual metric calculators
    # ------------------------------------------------------------------

    def _get_recent_matches(
        self, db: Session, team_id: int, before_date: datetime, n: int = _RECENT_MATCHES
    ) -> List[Match]:
        """Fetch the N most recent FINISHED matches for a team before a given date."""
        return (
            db.query(Match)
            .filter(
                and_(
                    or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
                    Match.status == "FINISHED",
                    Match.utc_date < before_date,
                )
            )
            .order_by(desc(Match.utc_date))
            .limit(n)
            .all()
        )

    def _get_match_stats(self, db: Session, match_id: int) -> Optional[MatchStatistic]:
        return (
            db.query(MatchStatistic).filter(MatchStatistic.match_id == match_id).first()
        )

    def _clamp(self, value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))

    def _safe_div(
        self, numerator: float, denominator: float, default: float = 0.0
    ) -> float:
        if not denominator:
            return default
        return numerator / denominator

    def _mean(self, values: List[float], default: float = 0.0) -> float:
        return sum(values) / len(values) if values else default

    def _normalize_rating(self, rating: Optional[float]) -> float:
        if rating is None:
            return 0.0
        return self._clamp((rating - 5.0) / 3.0)

    def _normalize_symmetric(
        self, value: float, negative_bound: float, positive_bound: float
    ) -> float:
        if positive_bound <= 0 or negative_bound <= 0:
            return 0.5
        if value >= 0:
            return self._clamp(0.5 + 0.5 * (value / positive_bound))
        return self._clamp(0.5 - 0.5 * (abs(value) / negative_bound))

    def _parse_lineup_players(self, lineup_blob: Optional[str]) -> Set[str]:
        if not lineup_blob:
            return set()
        try:
            parsed = json.loads(lineup_blob)
        except Exception:
            return {
                item.strip() for item in str(lineup_blob).split(",") if item.strip()
            }

        players: Set[str] = set()
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    candidate = (
                        item.get("player_name")
                        or item.get("name")
                        or item.get("player")
                    )
                    if candidate:
                        players.add(str(candidate).strip())
                elif item is not None:
                    players.add(str(item).strip())
        return players

    def _performance_sources(
        self, performances: List[PlayerMatchPerformance]
    ) -> Set[str]:
        sources: Set[str] = set()
        for perf in performances:
            if perf.statsbomb_id:
                sources.add("StatsBomb")
            if perf.fbref_id:
                sources.add("FBref")
            if perf.sofa_score_id or perf.sofa_score_rating is not None:
                sources.add("SofaScore")
        return sources

    def _team_recent_context(
        self, db: Session, team_id: int, match: Match
    ) -> Dict[str, Any]:
        recent_matches = self._get_recent_matches(db, team_id, match.utc_date)
        snapshots: List[Dict[str, Any]] = []
        sources: Set[str] = set()
        stats_sources: Set[str] = set()
        performance_sources: Set[str] = set()
        lineup_sources: Set[str] = set()
        event_sources: Set[str] = set()
        availability_sources: Set[str] = set()

        for recent_match in recent_matches:
            is_home = recent_match.home_team_id == team_id
            stats = self._get_match_stats(db, recent_match.id)
            lineup = (
                db.query(MatchLineup)
                .filter(
                    MatchLineup.match_id == recent_match.id,
                    MatchLineup.team_id == team_id,
                )
                .first()
            )
            performances = (
                db.query(PlayerMatchPerformance)
                .filter(
                    PlayerMatchPerformance.match_id == recent_match.id,
                    PlayerMatchPerformance.team_id == team_id,
                )
                .all()
            )
            events = (
                db.query(MatchEvent)
                .filter(
                    MatchEvent.match_id == recent_match.id,
                    MatchEvent.team_id == team_id,
                )
                .all()
            )

            if stats and stats.data_source:
                sources.add(stats.data_source)
                stats_sources.add(stats.data_source)
            perf_sources = self._performance_sources(performances)
            sources.update(perf_sources)
            performance_sources.update(perf_sources)
            if lineup:
                if lineup.coach_name == "StatsBomb Import":
                    sources.add("StatsBomb")
                    lineup_sources.add("StatsBomb")
                elif lineup.sofa_score_id:
                    sources.add("SofaScore")
                    lineup_sources.add("SofaScore")
            if events:
                if any((e.description or "").startswith("StatsBomb:") for e in events):
                    sources.add("StatsBomb")
                    event_sources.add("StatsBomb")
                if any(e.sofa_score_id for e in events):
                    sources.add("SofaScore")
                    event_sources.add("SofaScore")

            goals_for = (
                (recent_match.home_score or 0)
                if is_home
                else (recent_match.away_score or 0)
            )
            goals_against = (
                (recent_match.away_score or 0)
                if is_home
                else (recent_match.home_score or 0)
            )

            snapshots.append(
                {
                    "match": recent_match,
                    "is_home": is_home,
                    "stats": stats,
                    "lineup": lineup,
                    "performances": performances,
                    "events": events,
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                }
            )

        injuries = db.query(Injury).filter(Injury.team_id == team_id).all()
        suspensions = db.query(Suspension).filter(Suspension.team_id == team_id).all()
        nt_players = (
            db.query(NationalTeamPlayer)
            .filter(NationalTeamPlayer.team_id == team_id)
            .all()
        )
        if injuries:
            sources.add("Transfermarkt")
            availability_sources.add("Transfermarkt")
        if suspensions:
            sources.add("Transfermarkt")
            availability_sources.add("Transfermarkt")
        if nt_players:
            sources.add("Transfermarkt")
            availability_sources.add("Transfermarkt")

        return {
            "recent_matches": recent_matches,
            "snapshots": snapshots,
            "injuries": injuries,
            "suspensions": suspensions,
            "nt_players": nt_players,
            "sources": sorted(sources),
            "stats_sources": sorted(stats_sources),
            "performance_sources": sorted(performance_sources),
            "lineup_sources": sorted(lineup_sources),
            "event_sources": sorted(event_sources),
            "availability_sources": sorted(availability_sources),
        }

    def _build_team_engineered_metrics(
        self, db: Session, match: Match, team_id: int
    ) -> Dict[str, Any]:
        context = self._team_recent_context(db, team_id, match)
        snapshots = context["snapshots"]
        injuries = context["injuries"]
        suspensions = context["suspensions"]
        nt_players = context["nt_players"]

        wins = draws = losses = clean_sheets = 0
        goals_for: List[float] = []
        goals_against: List[float] = []
        goal_diff: List[float] = []
        xg_for: List[float] = []
        xg_against: List[float] = []
        xg_diff: List[float] = []
        shots: List[float] = []
        shots_on_target: List[float] = []
        passes: List[float] = []
        successful_passes: List[float] = []
        possession: List[float] = []
        pass_accuracy: List[float] = []
        tackles: List[float] = []
        interceptions: List[float] = []
        pressures: List[float] = []
        corners: List[float] = []
        aerial_duels: List[float] = []
        aerial_duels_won: List[float] = []
        blocks: List[float] = []
        gk_saves: List[float] = []
        gk_ratings: List[float] = []
        formations: List[str] = []
        lineup_sets: List[Set[str]] = []

        for snapshot in snapshots:
            recent_match = snapshot["match"]
            is_home = snapshot["is_home"]
            stats = snapshot["stats"]
            perfs = snapshot["performances"]
            lineup = snapshot["lineup"]

            gf = snapshot["goals_for"]
            ga = snapshot["goals_against"]
            goals_for.append(gf)
            goals_against.append(ga)
            goal_diff.append(gf - ga)
            if ga == 0:
                clean_sheets += 1

            if recent_match.winner == "DRAW":
                draws += 1
            elif recent_match.winner == ("HOME_TEAM" if is_home else "AWAY_TEAM"):
                wins += 1
            else:
                losses += 1

            if stats:
                team_xg_for = (
                    (stats.home_expected_goals or 0.0)
                    if is_home
                    else (stats.away_expected_goals or 0.0)
                )
                team_xg_against = (
                    (stats.away_expected_goals or 0.0)
                    if is_home
                    else (stats.home_expected_goals or 0.0)
                )
                xg_for.append(team_xg_for)
                xg_against.append(team_xg_against)
                xg_diff.append(team_xg_for - team_xg_against)
                shots.append(
                    (stats.home_shots or 0) if is_home else (stats.away_shots or 0)
                )
                shots_on_target.append(
                    (stats.home_shots_on_target or 0)
                    if is_home
                    else (stats.away_shots_on_target or 0)
                )
                passes.append(
                    (stats.home_passes or 0) if is_home else (stats.away_passes or 0)
                )
                successful_passes.append(
                    (stats.home_successful_passes or 0)
                    if is_home
                    else (stats.away_successful_passes or 0)
                )
                possession.append(
                    (stats.home_possession or 0.0)
                    if is_home
                    else (stats.away_possession or 0.0)
                )
                pass_accuracy.append(
                    (stats.home_pass_accuracy or 0.0)
                    if is_home
                    else (stats.away_pass_accuracy or 0.0)
                )
                tackles.append(
                    (stats.home_tackles or 0) if is_home else (stats.away_tackles or 0)
                )
                interceptions.append(
                    (stats.home_interceptions or 0)
                    if is_home
                    else (stats.away_interceptions or 0)
                )
                pressures.append(
                    (stats.home_pressures or 0)
                    if is_home
                    else (stats.away_pressures or 0)
                )
                corners.append(
                    (stats.home_corners or 0) if is_home else (stats.away_corners or 0)
                )
                aerial_duels.append(
                    (stats.home_aerial_duels or 0)
                    if is_home
                    else (stats.away_aerial_duels or 0)
                )

            if lineup and lineup.formation:
                formations.append(lineup.formation)
            lineup_players = self._parse_lineup_players(
                lineup.starting_xi if lineup else None
            )
            if lineup_players:
                lineup_sets.append(lineup_players)

            gk_perfs = [p for p in perfs if p.position and "GK" in p.position.upper()]
            if not gk_perfs:
                gk_perfs = [p for p in perfs if (p.saves or 0) > 0]
            if gk_perfs:
                gk_saves.append(sum(p.saves or 0 for p in gk_perfs))
                rated_gks = [
                    self._normalize_rating(p.rating or p.sofa_score_rating)
                    for p in gk_perfs
                    if (p.rating is not None or p.sofa_score_rating is not None)
                ]
                if rated_gks:
                    gk_ratings.append(self._mean(rated_gks))

            perf_aerial_total = sum(p.aerial_duels or 0 for p in perfs)
            perf_aerial_won = sum(p.aerial_duels_won or 0 for p in perfs)
            if perf_aerial_total > 0:
                aerial_duels.append(perf_aerial_total)
                aerial_duels_won.append(perf_aerial_won)
            perf_blocks = sum((p.blocks or 0) + (p.clearances or 0) for p in perfs)
            if perf_blocks > 0:
                blocks.append(perf_blocks)
            perf_pressures = sum(p.pressures or 0 for p in perfs)
            if perf_pressures > 0:
                pressures.append(perf_pressures)

        recent_count = len(snapshots)
        clean_sheet_rate = self._safe_div(clean_sheets, recent_count, 0.0)
        avg_goals_for = self._mean(goals_for)
        avg_goals_against = self._mean(goals_against)
        avg_goal_diff = self._mean(goal_diff)
        avg_xg_for = self._mean(xg_for)
        avg_xg_against = self._mean(xg_against)
        avg_xg_diff = self._mean(xg_diff)
        avg_shots = self._mean(shots)
        avg_shots_on_target = self._mean(shots_on_target)
        avg_passes = self._mean(passes)
        avg_successful_passes = self._mean(successful_passes)
        avg_possession = self._mean(possession)
        avg_pass_accuracy = self._mean(pass_accuracy)
        avg_tackles = self._mean(tackles)
        avg_interceptions = self._mean(interceptions)
        avg_pressures = self._mean(pressures)
        avg_corners = self._mean(corners)
        avg_aerial_duels = self._mean(aerial_duels)
        avg_aerial_duels_won = self._mean(aerial_duels_won)
        avg_blocks = self._mean(blocks)
        avg_gk_saves = self._mean(gk_saves)
        avg_gk_rating_score = self._mean(gk_ratings)

        points_ratio = self._safe_div((wins * 3) + draws, max(recent_count * 3, 1), 0.5)
        goal_diff_score = self._normalize_symmetric(avg_goal_diff, 2.0, 2.0)
        xg_diff_score = self._normalize_symmetric(avg_xg_diff, 1.5, 1.5)
        recent_form = (
            round(points_ratio * 0.5 + goal_diff_score * 0.25 + xg_diff_score * 0.25, 3)
            if recent_count
            else 0.5
        )

        gk_save_score = self._clamp(avg_gk_saves / 5.0)
        gk_clean_sheet_score = clean_sheet_rate
        gk_conceded_score = self._clamp(1.0 - (avg_goals_against / 3.0))
        goalkeeper_strength = (
            round(
                avg_gk_rating_score * 0.35
                + gk_save_score * 0.25
                + gk_clean_sheet_score * 0.20
                + gk_conceded_score * 0.20,
                3,
            )
            if recent_count
            else 0.0
        )

        passing_strength = (
            round(
                self._clamp(avg_pass_accuracy / 100.0) * 0.35
                + self._clamp(avg_passes / 700.0) * 0.20
                + self._clamp(avg_successful_passes / 600.0) * 0.25
                + self._clamp(avg_possession / 100.0) * 0.20,
                3,
            )
            if any(
                v > 0
                for v in [
                    avg_pass_accuracy,
                    avg_passes,
                    avg_successful_passes,
                    avg_possession,
                ]
            )
            else 0.0
        )

        aerial_win_pct = self._safe_div(avg_aerial_duels_won, avg_aerial_duels, 0.0)
        aerial_dominance = (
            round(
                aerial_win_pct * 0.70 + self._clamp(avg_aerial_duels / 25.0) * 0.30,
                3,
            )
            if avg_aerial_duels > 0
            else 0.0
        )

        pressing_strength = (
            round(
                self._clamp(avg_tackles / 25.0) * 0.30
                + self._clamp(avg_interceptions / 20.0) * 0.25
                + self._clamp(avg_pressures / 60.0) * 0.45,
                3,
            )
            if any(v > 0 for v in [avg_tackles, avg_interceptions, avg_pressures])
            else 0.0
        )

        defensive_stability = (
            round(
                clean_sheet_rate * 0.35
                + self._clamp(1.0 - (avg_xg_against / 2.5)) * 0.30
                + self._clamp(1.0 - (avg_goals_against / 3.0)) * 0.25
                + self._clamp(avg_blocks / 20.0) * 0.10,
                3,
            )
            if recent_count
            else 0.5
        )

        shots_on_target_rate = self._safe_div(avg_shots_on_target, avg_shots, 0.0)
        conversion_rate = self._safe_div(avg_goals_for, avg_shots, 0.0)
        goal_to_xg = self._safe_div(avg_goals_for, avg_xg_for, 0.0)
        attacking_efficiency = (
            round(
                self._clamp(avg_xg_for / 2.5) * 0.30
                + self._clamp(avg_goals_for / 3.0) * 0.30
                + self._clamp(shots_on_target_rate / 0.5) * 0.20
                + self._clamp(conversion_rate / 0.25) * 0.20,
                3,
            )
            if any(
                v > 0
                for v in [avg_xg_for, avg_goals_for, avg_shots_on_target, avg_shots]
            )
            else 0.0
        )

        finishing_quality = (
            round(
                self._clamp(goal_to_xg / 1.5) * 0.70
                + self._clamp(shots_on_target_rate / 0.5) * 0.30,
                3,
            )
            if any(
                v > 0
                for v in [avg_goals_for, avg_xg_for, avg_shots_on_target, avg_shots]
            )
            else 0.5
        )

        set_piece_strength = (
            round(
                self._clamp(avg_corners / 10.0) * 0.55 + aerial_win_pct * 0.45,
                3,
            )
            if any(v > 0 for v in [avg_corners, avg_aerial_duels])
            else 0.0
        )

        injured_names = {inj.player_name for inj in injuries if inj.player_name}
        suspended_names = {susp.player_name for susp in suspensions if susp.player_name}
        top_players = sorted(
            nt_players, key=lambda player: player.market_value or 0.0, reverse=True
        )
        top_starters = top_players[:11]
        unavailable_top_starters = sum(
            1
            for player in top_starters
            if player.player_name in injured_names
            or player.player_name in suspended_names
        )
        available_starters_ratio = self._safe_div(
            max(11 - unavailable_top_starters, 0), 11, 1.0
        )
        player_availability_score = self._safe_div(
            max(_SQUAD_SIZE - len(injuries) - len(suspensions), 0), _SQUAD_SIZE, 1.0
        )
        injury_impact_score = self._clamp(
            sum(injury.player_market_value or 0.0 for injury in injuries) / 100.0
        )
        suspension_impact_score = self._clamp(
            sum((susp.player_market_value or 0.0) for susp in suspensions) / 100.0
        )
        squad_availability = round(
            player_availability_score * 0.50
            + available_starters_ratio * 0.30
            + (1.0 - injury_impact_score) * 0.10
            + (1.0 - suspension_impact_score) * 0.10,
            3,
        )

        if formations:
            most_common_formation = max(set(formations), key=formations.count)
            formation_consistency = formations.count(most_common_formation) / len(
                formations
            )
        else:
            formation_consistency = 0.5

        lineup_overlaps: List[float] = []
        for previous_lineup, next_lineup in zip(lineup_sets, lineup_sets[1:]):
            union = previous_lineup | next_lineup
            if union:
                lineup_overlaps.append(len(previous_lineup & next_lineup) / len(union))
        lineup_consistency = self._mean(lineup_overlaps, 0.5)
        tactical_stability = round(
            formation_consistency * 0.55 + lineup_consistency * 0.45, 3
        )

        available = {
            "goalkeeper_strength": recent_count > 0,
            "passing_strength": bool(
                pass_accuracy or passes or successful_passes or possession
            ),
            "recent_form": recent_count > 0,
            "aerial_dominance": bool(aerial_duels),
            "pressing_strength": bool(tackles or interceptions or pressures),
            "defensive_stability": recent_count > 0,
            "attacking_efficiency": bool(
                xg_for or goals_for or shots or shots_on_target
            ),
            "finishing_quality": bool(xg_for or goals_for or shots or shots_on_target),
            "set_piece_strength": bool(corners or aerial_duels),
            "midfield_control": bool(
                pass_accuracy or possession or passes or successful_passes
            ),
            "squad_availability": True,
            "tactical_stability": bool(formations or lineup_sets),
        }

        raw_inputs = {
            "goalkeeper_strength": {
                "goalkeeper_rating_score": round(avg_gk_rating_score, 3),
                "saves_per_match": round(avg_gk_saves, 3),
                "clean_sheet_rate": round(clean_sheet_rate, 3),
                "goals_conceded_per_match": round(avg_goals_against, 3),
            },
            "passing_strength": {
                "pass_accuracy": round(avg_pass_accuracy, 3),
                "passes_per_match": round(avg_passes, 3),
                "successful_passes_per_match": round(avg_successful_passes, 3),
                "possession": round(avg_possession, 3),
            },
            "recent_form": {
                "recent_matches": recent_count,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "goal_difference_per_match": round(avg_goal_diff, 3),
                "xg_difference_per_match": round(avg_xg_diff, 3),
                "points_ratio": round(points_ratio, 3),
            },
            "aerial_dominance": {
                "aerial_duels_per_match": round(avg_aerial_duels, 3),
                "aerial_duels_won_per_match": round(avg_aerial_duels_won, 3),
                "aerial_win_pct": round(aerial_win_pct, 3),
            },
            "pressing_strength": {
                "tackles_per_match": round(avg_tackles, 3),
                "interceptions_per_match": round(avg_interceptions, 3),
                "pressures_per_match": round(avg_pressures, 3),
            },
            "defensive_stability": {
                "clean_sheet_rate": round(clean_sheet_rate, 3),
                "xga_per_match": round(avg_xg_against, 3),
                "goals_conceded_per_match": round(avg_goals_against, 3),
                "blocks_per_match": round(avg_blocks, 3),
            },
            "attacking_efficiency": {
                "goals_per_match": round(avg_goals_for, 3),
                "xg_per_match": round(avg_xg_for, 3),
                "shots_per_match": round(avg_shots, 3),
                "shots_on_target_per_match": round(avg_shots_on_target, 3),
                "conversion_rate": round(conversion_rate, 3),
            },
            "finishing_quality": {
                "goals_per_xg": round(goal_to_xg, 3),
                "shots_on_target_rate": round(shots_on_target_rate, 3),
                "big_chances_scored": None,
            },
            "set_piece_strength": {
                "corners_per_match": round(avg_corners, 3),
                "aerial_win_pct": round(aerial_win_pct, 3),
            },
            "midfield_control": {
                "pass_accuracy": round(avg_pass_accuracy, 3),
                "successful_passes_per_match": round(avg_successful_passes, 3),
                "passes_per_match": round(avg_passes, 3),
                "possession": round(avg_possession, 3),
            },
            "squad_availability": {
                "injuries": len(injuries),
                "suspensions": len(suspensions),
                "available_starters_ratio": round(available_starters_ratio, 3),
                "player_availability_score": round(player_availability_score, 3),
                "injury_impact_score": round(injury_impact_score, 3),
                "suspension_impact_score": round(suspension_impact_score, 3),
            },
            "tactical_stability": {
                "formation_consistency": round(formation_consistency, 3),
                "lineup_consistency": round(lineup_consistency, 3),
                "recent_formations": formations,
            },
        }

        stats_source_set = set(context["stats_sources"])
        performance_source_set = set(context["performance_sources"])
        lineup_source_set = set(context["lineup_sources"])
        availability_source_set = set(context["availability_sources"])
        providers = {
            "goalkeeper_strength": sorted({"FootballData"} | performance_source_set),
            "passing_strength": sorted(stats_source_set),
            "recent_form": sorted({"FootballData"} | stats_source_set),
            "aerial_dominance": sorted(stats_source_set | performance_source_set),
            "pressing_strength": sorted(stats_source_set | performance_source_set),
            "defensive_stability": sorted(
                {"FootballData"} | stats_source_set | performance_source_set
            ),
            "attacking_efficiency": sorted({"FootballData"} | stats_source_set),
            "finishing_quality": sorted({"FootballData"} | stats_source_set),
            "set_piece_strength": sorted(stats_source_set | performance_source_set),
            "midfield_control": sorted(stats_source_set),
            "squad_availability": sorted(availability_source_set or {"Transfermarkt"}),
            "tactical_stability": sorted(lineup_source_set),
        }

        return {
            "goalkeeper_strength": goalkeeper_strength,
            "passing_strength": passing_strength,
            "recent_form": recent_form,
            "aerial_dominance": aerial_dominance,
            "pressing_strength": pressing_strength,
            "defensive_stability": defensive_stability,
            "attacking_efficiency": attacking_efficiency,
            "finishing_quality": finishing_quality,
            "set_piece_strength": set_piece_strength,
            "midfield_control": round(
                self._clamp(avg_pass_accuracy / 100.0) * 0.40
                + self._clamp(avg_successful_passes / 600.0) * 0.20
                + self._clamp(avg_passes / 700.0) * 0.15
                + self._clamp(avg_possession / 100.0) * 0.25,
                3,
            )
            if any(
                v > 0
                for v in [
                    avg_pass_accuracy,
                    avg_successful_passes,
                    avg_passes,
                    avg_possession,
                ]
            )
            else 0.0,
            "squad_availability": squad_availability,
            "tactical_stability": tactical_stability,
            "raw_inputs": raw_inputs,
            "providers": providers,
            "available": available,
        }

    def _calc_attacking_strength(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """Avg shots + weighted xG over recent matches."""
        home_scores, away_scores = [], []
        for team_id, scores in [
            (match.home_team_id, home_scores),
            (match.away_team_id, away_scores),
        ]:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            for m in recent:
                stats = self._get_match_stats(db, m.id)
                if stats:
                    is_home = m.home_team_id == team_id
                    shots = (
                        (stats.home_shots or 0) if is_home else (stats.away_shots or 0)
                    )
                    xg = (
                        (stats.home_expected_goals or 0.0)
                        if is_home
                        else (stats.away_expected_goals or 0.0)
                    )
                    score = min((shots * 0.05) + (xg * 0.5), 2.0)
                    scores.append(score)
            home = (
                round(min(sum(home_scores) / len(home_scores), 2.0), 3)
                if home_scores
                else 0.0
            )
            away = (
                round(min(sum(away_scores) / len(away_scores), 2.0), 3)
                if away_scores
                else 0.0
            )
        return home, away

    def _calc_defensive_strength(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """Inverse of goals conceded rate + clean sheet bonus."""

        def _team_def(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            if not recent:
                return 0.5  # neutral
            conceded = []
            clean_sheets = 0
            for m in recent:
                is_home = m.home_team_id == team_id
                gc = (m.away_score or 0) if is_home else (m.home_score or 0)
                conceded.append(gc)
                if gc == 0:
                    clean_sheets += 1
            avg_conceded = sum(conceded) / len(conceded)
            cs_rate = clean_sheets / len(recent)
            # Scale: 0 goals conceded = 1.0, 3+ goals = 0.0
            return round(max(0.0, 1.0 - (avg_conceded / 3.0)) * 0.7 + cs_rate * 0.3, 3)

        return _team_def(match.home_team_id), _team_def(match.away_team_id)

    def _calc_midfield_control(self, db: Session, match: Match) -> Tuple[float, float]:
        """Pass accuracy + possession + passing volume control score."""
        stats = self._get_match_stats(db, match.id)
        if stats:
            home = round(
                self._clamp((stats.home_pass_accuracy or 0.0) / 100.0) * 0.40
                + self._clamp((stats.home_successful_passes or 0.0) / 600.0) * 0.20
                + self._clamp((stats.home_passes or 0.0) / 700.0) * 0.15
                + self._clamp((stats.home_possession or 50.0) / 100.0) * 0.25,
                3,
            )
            away = round(
                self._clamp((stats.away_pass_accuracy or 0.0) / 100.0) * 0.40
                + self._clamp((stats.away_successful_passes or 0.0) / 600.0) * 0.20
                + self._clamp((stats.away_passes or 0.0) / 700.0) * 0.15
                + self._clamp((stats.away_possession or 50.0) / 100.0) * 0.25,
                3,
            )
            if home > 0 or away > 0:
                return home, away

        def _team_mid(team_id: int) -> float:
            engineered = self._build_team_engineered_metrics(db, match, team_id)
            return engineered["midfield_control"]

        return _team_mid(match.home_team_id), _team_mid(match.away_team_id)

    def _calc_goalkeeper_performance(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """Average saves per match from PlayerMatchPerformance."""

        def _gk_saves(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            save_list = []
            for m in recent:
                gk_perfs = (
                    db.query(PlayerMatchPerformance)
                    .filter(
                        PlayerMatchPerformance.match_id == m.id,
                        PlayerMatchPerformance.team_id == team_id,
                        PlayerMatchPerformance.position.ilike("%GK%"),
                    )
                    .all()
                )
                if gk_perfs:
                    total_saves = sum(p.saves or 0 for p in gk_perfs)
                    save_list.append(total_saves)
            if not save_list:
                return 0.0
            avg = sum(save_list) / len(save_list)
            return round(min(avg / 10.0, 1.0), 3)  # normalize: 10 saves ≈ 1.0

        return _gk_saves(match.home_team_id), _gk_saves(match.away_team_id)

    def _calc_passing_dominance(self, db: Session, match: Match) -> Tuple[float, float]:
        """Total passes + accuracy weighted score."""
        stats = self._get_match_stats(db, match.id)
        if stats:
            total = (stats.home_passes or 0) + (stats.away_passes or 0)
            if total == 0:
                return 0.0, 0.0
            home_share = (stats.home_passes or 0) / total
            away_share = (stats.away_passes or 0) / total
            home_pa = (stats.home_pass_accuracy or 0.0) / 100.0
            away_pa = (stats.away_pass_accuracy or 0.0) / 100.0
            return round(home_share * 0.5 + home_pa * 0.5, 3), round(
                away_share * 0.5 + away_pa * 0.5, 3
            )
        return 0.0, 0.0

    def _calc_pressing_intensity(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """Tackles + interceptions per match (from MatchStatistic)."""

        def _press(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            vals = []
            for m in recent:
                s = self._get_match_stats(db, m.id)
                if s:
                    is_home = m.home_team_id == team_id
                    tackles = (
                        (s.home_tackles or 0) if is_home else (s.away_tackles or 0)
                    )
                    interceptions = (
                        (s.home_interceptions or 0)
                        if is_home
                        else (s.away_interceptions or 0)
                    )
                    total = tackles + interceptions
                    vals.append(total)
            if not vals:
                return 0.0
            avg = sum(vals) / len(vals)
            return round(
                min(avg / 30.0, 1.0), 3
            )  # normalize: 30 combined actions ≈ 1.0

        # Also check current match stats
        stats = self._get_match_stats(db, match.id)
        if stats:
            home_pi = min(
                ((stats.home_tackles or 0) + (stats.home_interceptions or 0)) / 30.0,
                1.0,
            )
            away_pi = min(
                ((stats.away_tackles or 0) + (stats.away_interceptions or 0)) / 30.0,
                1.0,
            )
            if home_pi > 0 or away_pi > 0:
                return round(home_pi, 3), round(away_pi, 3)

        return _press(match.home_team_id), _press(match.away_team_id)

    def _calc_set_piece_threat(self, db: Session, match: Match) -> Tuple[float, float]:
        """Average corners per match as proxy for set-piece threat."""

        def _sp(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            corners_list = []
            for m in recent:
                s = self._get_match_stats(db, m.id)
                if s:
                    is_home = m.home_team_id == team_id
                    corners = (
                        (s.home_corners or 0) if is_home else (s.away_corners or 0)
                    )
                    corners_list.append(corners)
            if not corners_list:
                return 0.0
            avg = sum(corners_list) / len(corners_list)
            return round(min(avg / 12.0, 1.0), 3)  # normalize: 12 corners ≈ 1.0

        return _sp(match.home_team_id), _sp(match.away_team_id)

    def _calc_discipline_score(self, db: Session, match: Match) -> Tuple[float, float]:
        """Inverse of cards per match. More cards = lower score."""

        def _disc(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            if not recent:
                return 1.0  # neutral
            card_list = []
            for m in recent:
                is_home = m.home_team_id == team_id
                yellows = (
                    (m.home_yellow_cards or 0)
                    if is_home
                    else (m.away_yellow_cards or 0)
                )
                reds = (m.home_red_cards or 0) if is_home else (m.away_red_cards or 0)
                weighted_cards = yellows + reds * 3
                card_list.append(weighted_cards)
            avg = sum(card_list) / len(card_list)
            return round(max(0.0, 1.0 - (avg / 6.0)), 3)  # 0 cards = 1.0, 6+ = 0.0

        return _disc(match.home_team_id), _disc(match.away_team_id)

    def _calc_fatigue_score(self, db: Session, match: Match) -> Tuple[float, float]:
        """
        Days since last match (less rest = more fatigue = lower score).
        Score: 0=fatigued (0 days rest), 1=fresh (14+ days rest).
        """

        def _fatigue(team_id: int) -> float:
            last = self._get_recent_matches(db, team_id, match.utc_date, n=1)
            if not last:
                return 1.0  # unknown → assume fresh
            days_rest = (match.utc_date - last[0].utc_date).days
            return round(min(days_rest / 14.0, 1.0), 3)

        return _fatigue(match.home_team_id), _fatigue(match.away_team_id)

    def _calc_substitution_impact(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """
        Difference in avg performance rating between starters and substitutes.
        Positive = substitutes improved the team.
        """

        def _sub_impact(team_id: int) -> float:
            starters = (
                db.query(PlayerMatchPerformance)
                .filter(
                    PlayerMatchPerformance.match_id == match.id,
                    PlayerMatchPerformance.team_id == team_id,
                    PlayerMatchPerformance.is_starter == 1,
                    PlayerMatchPerformance.sofa_score_rating.isnot(None),
                )
                .all()
            )
            subs = (
                db.query(PlayerMatchPerformance)
                .filter(
                    PlayerMatchPerformance.match_id == match.id,
                    PlayerMatchPerformance.team_id == team_id,
                    PlayerMatchPerformance.is_starter == 0,
                    PlayerMatchPerformance.sofa_score_rating.isnot(None),
                )
                .all()
            )
            if not starters or not subs:
                return 0.0
            avg_starter = sum(p.sofa_score_rating for p in starters) / len(starters)
            avg_sub = sum(p.sofa_score_rating for p in subs) / len(subs)
            return round(
                (avg_sub - avg_starter) / 10.0, 3
            )  # normalize SofaScore 0-10 range

        return _sub_impact(match.home_team_id), _sub_impact(match.away_team_id)

    def _calc_player_availability(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """
        (squad_size - injured - suspended) / squad_size for each team.
        """

        def _avail(team_id: int) -> float:
            injured = db.query(Injury).filter(Injury.team_id == team_id).count()
            suspended = (
                db.query(Suspension)
                .filter(
                    Suspension.team_id == team_id,
                    Suspension.status.in_(["PENDING", "OFFICIAL"]),
                )
                .count()
            )
            missing = injured + suspended
            return round(max(0.0, (_SQUAD_SIZE - missing) / _SQUAD_SIZE), 3)

        return _avail(match.home_team_id), _avail(match.away_team_id)

    def _calc_injury_impact(self, db: Session, match: Match) -> Tuple[float, float]:
        """Sum of market values of injured players (normalized by squad avg value)."""

        def _inj_mv(team_id: int) -> float:
            injuries = db.query(Injury).filter(Injury.team_id == team_id).all()
            if not injuries:
                return 0.0
            # Try to get player market values from NationalTeamPlayer
            total_mv = 0.0
            for inj in injuries:
                if inj.player_name:
                    nt_player = (
                        db.query(NationalTeamPlayer)
                        .filter(
                            NationalTeamPlayer.team_id == team_id,
                            NationalTeamPlayer.player_name.ilike(
                                f"%{inj.player_name}%"
                            ),
                        )
                        .first()
                    )
                    if nt_player and nt_player.market_value:
                        total_mv += nt_player.market_value
            # Normalize: 100M market value loss ≈ 1.0
            return round(min(total_mv / 100_000_000, 1.0), 3)

        return _inj_mv(match.home_team_id), _inj_mv(match.away_team_id)

    def _calc_suspension_impact(self, db: Session, match: Match) -> Tuple[float, float]:
        """Number of suspended players (normalized by squad size)."""

        def _susp(team_id: int) -> float:
            count = (
                db.query(Suspension)
                .filter(
                    Suspension.team_id == team_id,
                    Suspension.status.in_(["PENDING", "OFFICIAL"]),
                )
                .count()
            )
            return round(min(count / _SQUAD_SIZE, 1.0), 3)

        return _susp(match.home_team_id), _susp(match.away_team_id)

    def _calc_formation_stability(
        self, db: Session, match: Match
    ) -> Tuple[float, float]:
        """
        Fraction of recent matches using the same formation.
        Higher = more stable tactical setup.
        """

        def _form_stab(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            if not recent:
                return 0.5  # unknown
            formations = []
            for m in recent:
                lineup = (
                    db.query(MatchLineup)
                    .filter(
                        MatchLineup.match_id == m.id,
                        MatchLineup.team_id == team_id,
                    )
                    .first()
                )
                if lineup and lineup.formation:
                    formations.append(lineup.formation)
            if not formations:
                return 0.5
            most_common = max(set(formations), key=formations.count)
            return round(formations.count(most_common) / len(formations), 3)

        return _form_stab(match.home_team_id), _form_stab(match.away_team_id)

    def _calc_momentum_score(self, db: Session, match: Match) -> Tuple[float, float]:
        """
        Weighted recent results: win=1, draw=0.5, loss=0.
        Most recent matches get higher weight.
        """

        def _momentum(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            if not recent:
                return 0.5
            weighted_sum = 0.0
            total_weight = 0.0
            for i, m in enumerate(recent):
                weight = _FORM_WEIGHTS[i] if i < len(_FORM_WEIGHTS) else 0.05
                is_home = m.home_team_id == team_id
                if m.winner == ("HOME_TEAM" if is_home else "AWAY_TEAM"):
                    result = 1.0
                elif m.winner == "DRAW":
                    result = 0.5
                else:
                    result = 0.0
                weighted_sum += weight * result
                total_weight += weight
            return round(weighted_sum / total_weight if total_weight > 0 else 0.5, 3)

        return _momentum(match.home_team_id), _momentum(match.away_team_id)

    def _calc_confidence_score(self, intel: MatchIntelligence) -> float:
        """
        Weighted composite of all computed scores.
        Components and weights are tuned for football prediction relevance.
        """
        components = [
            (intel.home_attacking_strength - intel.away_attacking_strength, 0.15),
            (intel.home_defensive_strength - intel.away_defensive_strength, 0.12),
            (intel.home_midfield_control - intel.away_midfield_control, 0.10),
            (intel.home_passing_dominance - intel.away_passing_dominance, 0.08),
            (
                intel.home_goalkeeper_performance - intel.away_goalkeeper_performance,
                0.08,
            ),
            (intel.home_pressing_intensity - intel.away_pressing_intensity, 0.06),
            (intel.home_momentum_score - intel.away_momentum_score, 0.15),
            (
                intel.home_player_availability_score
                - intel.away_player_availability_score,
                0.10,
            ),
            (intel.home_discipline_score - intel.away_discipline_score, 0.06),
            ((intel.home_fatigue_score - intel.away_fatigue_score), 0.05),
            (intel.home_formation_stability - intel.away_formation_stability, 0.05),
        ]
        total = sum(v * w for v, w in components)
        # Normalize to 0-1 range (input diffs range from -1 to +1)
        return round((total + 1.0) / 2.0, 3)

    def explain_engineered_features(self, db: Session, match: Match) -> Dict[str, Any]:
        """Return raw inputs, calculated value, and contributing providers for engineered ML features."""
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
        home_data = self._build_team_engineered_metrics(db, match, match.home_team_id)
        away_data = self._build_team_engineered_metrics(db, match, match.away_team_id)
        feature_names = [
            "goalkeeper_strength",
            "passing_strength",
            "recent_form",
            "aerial_dominance",
            "pressing_strength",
            "defensive_stability",
            "attacking_efficiency",
            "finishing_quality",
            "set_piece_strength",
            "midfield_control",
            "squad_availability",
            "tactical_stability",
        ]
        features: Dict[str, Any] = {}
        for name in feature_names:
            features[name] = {
                "home": {
                    "team": getattr(home_team, "name", str(match.home_team_id)),
                    "value": home_data[name],
                    "raw_inputs": home_data["raw_inputs"].get(name, {}),
                    "providers": home_data["providers"].get(name, []),
                    "available": home_data["available"].get(name, False),
                },
                "away": {
                    "team": getattr(away_team, "name", str(match.away_team_id)),
                    "value": away_data[name],
                    "raw_inputs": away_data["raw_inputs"].get(name, {}),
                    "providers": away_data["providers"].get(name, []),
                    "available": away_data["available"].get(name, False),
                },
                "diff": round(home_data[name] - away_data[name], 3),
            }
        return {
            "match_id": match.id,
            "fixture": f"{getattr(home_team, 'name', '?')} vs {getattr(away_team, 'name', '?')}",
            "features": features,
        }

    def _detect_sources(self, db: Session, match: Match) -> List[str]:
        """Detect which data sources contributed to this match."""
        sources = ["Database"]
        if db.query(MatchStatistic).filter(MatchStatistic.match_id == match.id).first():
            sources.append("MatchStatistics")
        if (
            db.query(PlayerMatchPerformance)
            .filter(PlayerMatchPerformance.match_id == match.id)
            .count()
            > 0
        ):
            sources.append("PlayerPerformances")
        if db.query(MatchLineup).filter(MatchLineup.match_id == match.id).count() > 0:
            sources.append("Lineups")
        return sources

    def to_features_dict(self, intelligence: MatchIntelligence) -> Dict[str, Any]:
        """
        Convert a MatchIntelligence object to a flat features dictionary
        compatible with the ML pipeline.
        """
        return {
            # Attacking
            "home_attacking_strength": intelligence.home_attacking_strength,
            "away_attacking_strength": intelligence.away_attacking_strength,
            "attacking_strength_diff": intelligence.home_attacking_strength
            - intelligence.away_attacking_strength,
            # Defensive
            "home_defensive_strength": intelligence.home_defensive_strength,
            "away_defensive_strength": intelligence.away_defensive_strength,
            "defensive_strength_diff": intelligence.home_defensive_strength
            - intelligence.away_defensive_strength,
            # Midfield
            "home_midfield_control": intelligence.home_midfield_control,
            "away_midfield_control": intelligence.away_midfield_control,
            "midfield_control_diff": intelligence.home_midfield_control
            - intelligence.away_midfield_control,
            # Goalkeeper
            "home_goalkeeper_performance": intelligence.home_goalkeeper_performance,
            "away_goalkeeper_performance": intelligence.away_goalkeeper_performance,
            "goalkeeper_performance_diff": intelligence.home_goalkeeper_performance
            - intelligence.away_goalkeeper_performance,
            # Passing
            "home_passing_dominance": intelligence.home_passing_dominance,
            "away_passing_dominance": intelligence.away_passing_dominance,
            "passing_dominance_diff": intelligence.home_passing_dominance
            - intelligence.away_passing_dominance,
            # Pressing
            "home_pressing_intensity": intelligence.home_pressing_intensity,
            "away_pressing_intensity": intelligence.away_pressing_intensity,
            "pressing_intensity_diff": intelligence.home_pressing_intensity
            - intelligence.away_pressing_intensity,
            # Set pieces
            "home_set_piece_threat": intelligence.home_set_piece_threat,
            "away_set_piece_threat": intelligence.away_set_piece_threat,
            "set_piece_threat_diff": intelligence.home_set_piece_threat
            - intelligence.away_set_piece_threat,
            # Discipline
            "home_discipline_score": intelligence.home_discipline_score,
            "away_discipline_score": intelligence.away_discipline_score,
            "discipline_score_diff": intelligence.home_discipline_score
            - intelligence.away_discipline_score,
            # Fatigue
            "home_fatigue_score": intelligence.home_fatigue_score,
            "away_fatigue_score": intelligence.away_fatigue_score,
            "fatigue_score_diff": intelligence.home_fatigue_score
            - intelligence.away_fatigue_score,
            # Substitution
            "home_substitution_impact": intelligence.home_substitution_impact,
            "away_substitution_impact": intelligence.away_substitution_impact,
            "substitution_impact_diff": intelligence.home_substitution_impact
            - intelligence.away_substitution_impact,
            # Availability
            "home_player_availability_score": intelligence.home_player_availability_score,
            "away_player_availability_score": intelligence.away_player_availability_score,
            "availability_score_diff": intelligence.home_player_availability_score
            - intelligence.away_player_availability_score,
            # Injury / Suspension
            "home_injury_impact": intelligence.home_injury_impact,
            "away_injury_impact": intelligence.away_injury_impact,
            "injury_impact_diff": intelligence.home_injury_impact
            - intelligence.away_injury_impact,
            "home_suspension_impact": intelligence.home_suspension_impact,
            "away_suspension_impact": intelligence.away_suspension_impact,
            "suspension_impact_diff": intelligence.home_suspension_impact
            - intelligence.away_suspension_impact,
            # Formation
            "home_formation_stability": intelligence.home_formation_stability,
            "away_formation_stability": intelligence.away_formation_stability,
            "formation_stability_diff": intelligence.home_formation_stability
            - intelligence.away_formation_stability,
            # Momentum
            "home_momentum_score": intelligence.home_momentum_score,
            "away_momentum_score": intelligence.away_momentum_score,
            "momentum_score_diff": intelligence.home_momentum_score
            - intelligence.away_momentum_score,
            # Additional engineered ML-only features
            "home_goalkeeper_strength": intelligence.home_goalkeeper_strength,
            "away_goalkeeper_strength": intelligence.away_goalkeeper_strength,
            "goalkeeper_strength_diff": intelligence.home_goalkeeper_strength
            - intelligence.away_goalkeeper_strength,
            "home_passing_strength": intelligence.home_passing_strength,
            "away_passing_strength": intelligence.away_passing_strength,
            "passing_strength_diff": intelligence.home_passing_strength
            - intelligence.away_passing_strength,
            "home_recent_form": intelligence.home_recent_form,
            "away_recent_form": intelligence.away_recent_form,
            "recent_form_diff": intelligence.home_recent_form
            - intelligence.away_recent_form,
            "home_aerial_dominance": intelligence.home_aerial_dominance,
            "away_aerial_dominance": intelligence.away_aerial_dominance,
            "aerial_dominance_diff": intelligence.home_aerial_dominance
            - intelligence.away_aerial_dominance,
            "home_pressing_strength": intelligence.home_pressing_strength,
            "away_pressing_strength": intelligence.away_pressing_strength,
            "pressing_strength_diff": intelligence.home_pressing_strength
            - intelligence.away_pressing_strength,
            "home_defensive_stability": intelligence.home_defensive_stability,
            "away_defensive_stability": intelligence.away_defensive_stability,
            "defensive_stability_diff": intelligence.home_defensive_stability
            - intelligence.away_defensive_stability,
            "home_attacking_efficiency": intelligence.home_attacking_efficiency,
            "away_attacking_efficiency": intelligence.away_attacking_efficiency,
            "attacking_efficiency_diff": intelligence.home_attacking_efficiency
            - intelligence.away_attacking_efficiency,
            "home_finishing_quality": intelligence.home_finishing_quality,
            "away_finishing_quality": intelligence.away_finishing_quality,
            "finishing_quality_diff": intelligence.home_finishing_quality
            - intelligence.away_finishing_quality,
            "home_set_piece_strength": intelligence.home_set_piece_strength,
            "away_set_piece_strength": intelligence.away_set_piece_strength,
            "set_piece_strength_diff": intelligence.home_set_piece_strength
            - intelligence.away_set_piece_strength,
            "home_squad_availability": intelligence.home_squad_availability,
            "away_squad_availability": intelligence.away_squad_availability,
            "squad_availability_diff": intelligence.home_squad_availability
            - intelligence.away_squad_availability,
            "home_tactical_stability": intelligence.home_tactical_stability,
            "away_tactical_stability": intelligence.away_tactical_stability,
            "tactical_stability_diff": intelligence.home_tactical_stability
            - intelligence.away_tactical_stability,
            # Composite
            "confidence_score": intelligence.confidence_score,
            "data_completeness": intelligence.data_completeness,
        }

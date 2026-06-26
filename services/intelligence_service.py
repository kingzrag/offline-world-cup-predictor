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

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

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
        """Pass accuracy + possession differential from MatchStatistic."""
        stats = self._get_match_stats(db, match.id)
        if stats:
            home_pa = (stats.home_pass_accuracy or 0.0) / 100.0
            away_pa = (stats.away_pass_accuracy or 0.0) / 100.0
            home_pos = (stats.home_possession or 50.0) / 100.0
            away_pos = (stats.away_possession or 50.0) / 100.0
            home = round((home_pa * 0.5 + home_pos * 0.5), 3)
            away = round((away_pa * 0.5 + away_pos * 0.5), 3)
            return home, away

        # Fallback: look at last N matches
        def _team_mid(team_id: int) -> float:
            recent = self._get_recent_matches(db, team_id, match.utc_date)
            vals = []
            for m in recent:
                s = self._get_match_stats(db, m.id)
                if s:
                    is_home = m.home_team_id == team_id
                    pa = (
                        (s.home_pass_accuracy or 0)
                        if is_home
                        else (s.away_pass_accuracy or 0)
                    ) / 100.0
                    pos = (
                        (s.home_possession or 50)
                        if is_home
                        else (s.away_possession or 50)
                    ) / 100.0
                    vals.append(pa * 0.5 + pos * 0.5)
            return round(sum(vals) / len(vals), 3) if vals else 0.0

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
            # Composite
            "confidence_score": intelligence.confidence_score,
            "data_completeness": intelligence.data_completeness,
        }

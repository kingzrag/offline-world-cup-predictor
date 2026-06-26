#!/usr/bin/env python3
"""
Detect and repair common provider-pipeline data quality issues.

Repairs performed when safely derivable:
- duplicate matches by natural key
- duplicate players by team/name
- duplicate match statistics by match_id
- duplicate lineups by match_id/team_id
- duplicate player performances by source key or player name
- missing match winner from scores
- missing match formations from lineups
- missing match possession/xG from match_statistics
- missing pass accuracy from passes + successful_passes
- missing player_id on performances by team/name lookup
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func

from database.connection import SessionLocal
from models import (
    Match,
    MatchEvent,
    MatchLineup,
    MatchStatistic,
    Player,
    PlayerMatchPerformance,
    Prediction,
)


@dataclass
class RepairSummary:
    duplicate_match_groups: int = 0
    duplicate_player_groups: int = 0
    duplicate_statistics_groups: int = 0
    duplicate_lineup_groups: int = 0
    duplicate_performance_groups: int = 0
    duplicate_match_conflict_groups: int = 0
    matches_merged: int = 0
    players_merged: int = 0
    statistics_merged: int = 0
    lineups_merged: int = 0
    performances_merged: int = 0
    winners_derived: int = 0
    formations_derived: int = 0
    match_stats_backfilled: int = 0
    match_pass_accuracy_derived: int = 0
    player_pass_accuracy_derived: int = 0
    player_links_filled: int = 0


def _merge_scalar(target, source, field_names: Sequence[str]) -> None:
    for field_name in field_names:
        if getattr(target, field_name) in (None, "", 0):
            source_value = getattr(source, field_name)
            if source_value not in (None, "", 0):
                setattr(target, field_name, source_value)


def _keep_lowest(rows):
    return sorted(rows, key=lambda row: row.id)[0]


def merge_duplicate_match_statistics(db, summary: RepairSummary) -> None:
    groups = (
        db.query(MatchStatistic.match_id, func.count(MatchStatistic.id))
        .group_by(MatchStatistic.match_id)
        .having(func.count(MatchStatistic.id) > 1)
        .all()
    )
    summary.duplicate_statistics_groups = len(groups)

    stats_fields = [
        column.name
        for column in MatchStatistic.__table__.columns
        if column.name not in {"id", "match_id", "created_at", "updated_at"}
    ]

    for match_id, _ in groups:
        rows = (
            db.query(MatchStatistic)
            .filter(MatchStatistic.match_id == match_id)
            .order_by(MatchStatistic.id)
            .all()
        )
        keep = rows[0]
        for row in rows[1:]:
            _merge_scalar(keep, row, stats_fields)
            db.delete(row)
            summary.statistics_merged += 1


def merge_duplicate_lineups(db, summary: RepairSummary) -> None:
    groups = (
        db.query(MatchLineup.match_id, MatchLineup.team_id, func.count(MatchLineup.id))
        .group_by(MatchLineup.match_id, MatchLineup.team_id)
        .having(func.count(MatchLineup.id) > 1)
        .all()
    )
    summary.duplicate_lineup_groups = len(groups)

    for match_id, team_id, _ in groups:
        rows = (
            db.query(MatchLineup)
            .filter(MatchLineup.match_id == match_id, MatchLineup.team_id == team_id)
            .order_by(MatchLineup.id)
            .all()
        )
        keep = rows[0]
        for row in rows[1:]:
            _merge_scalar(
                keep,
                row,
                [
                    "formation",
                    "starting_xi",
                    "substitutes",
                    "coach_name",
                    "sofa_score_id",
                ],
            )
            db.delete(row)
            summary.lineups_merged += 1


def _performance_identity(perf: PlayerMatchPerformance) -> str:
    if perf.statsbomb_id:
        return f"statsbomb:{perf.statsbomb_id}"
    if perf.sofa_score_id:
        return f"sofascore:{perf.sofa_score_id}"
    name = (perf.player_name or "").strip().lower()
    return f"name:{name}"


def merge_duplicate_performances(db, summary: RepairSummary) -> None:
    grouped: Dict[Tuple[int, int, str], List[PlayerMatchPerformance]] = defaultdict(
        list
    )
    rows = db.query(PlayerMatchPerformance).order_by(PlayerMatchPerformance.id).all()
    for row in rows:
        grouped[(row.match_id, row.team_id, _performance_identity(row))].append(row)

    duplicates = [group for group in grouped.values() if len(group) > 1]
    summary.duplicate_performance_groups = len(duplicates)

    fields = [
        "player_id",
        "player_name",
        "position",
        "is_starter",
        "minutes_played",
        "goals",
        "assists",
        "shots",
        "shots_on_target",
        "passes",
        "successful_passes",
        "pass_accuracy",
        "tackles",
        "interceptions",
        "saves",
        "fouls_committed",
        "fouls_drawn",
        "yellow_cards",
        "red_cards",
        "offsides",
        "corners",
        "aerial_duels",
        "aerial_duels_won",
        "key_passes",
        "pressures",
        "carries",
        "dribbles_completed",
        "clearances",
        "blocks",
        "sofa_score_id",
        "sofa_score_rating",
        "fbref_id",
        "statsbomb_id",
        "statsbomb_xg",
    ]

    for group in duplicates:
        keep = group[0]
        for row in group[1:]:
            _merge_scalar(keep, row, fields)
            db.delete(row)
            summary.performances_merged += 1


def merge_duplicate_players(db, summary: RepairSummary) -> None:
    groups = (
        db.query(
            Player.team_id,
            func.lower(Player.name).label("lower_name"),
            func.count(Player.id),
        )
        .group_by(Player.team_id, func.lower(Player.name))
        .having(func.count(Player.id) > 1)
        .all()
    )
    summary.duplicate_player_groups = len(groups)

    fields = ["api_id", "position", "date_of_birth", "nationality", "role"]

    for team_id, lower_name, _ in groups:
        players = (
            db.query(Player)
            .filter(Player.team_id == team_id, func.lower(Player.name) == lower_name)
            .order_by(Player.id)
            .all()
        )
        keep = players[0]
        for player in players[1:]:
            _merge_scalar(keep, player, fields)
            (
                db.query(PlayerMatchPerformance)
                .filter(PlayerMatchPerformance.player_id == player.id)
                .update(
                    {PlayerMatchPerformance.player_id: keep.id},
                    synchronize_session=False,
                )
            )
            db.delete(player)
            summary.players_merged += 1


def merge_duplicate_matches(db, summary: RepairSummary) -> None:
    groups = (
        db.query(
            Match.competition_id,
            Match.home_team_id,
            Match.away_team_id,
            Match.utc_date,
            func.count(Match.id),
        )
        .group_by(
            Match.competition_id, Match.home_team_id, Match.away_team_id, Match.utc_date
        )
        .having(func.count(Match.id) > 1)
        .all()
    )
    summary.duplicate_match_groups = len(groups)

    unique_provider_fields = [
        "api_id",
        "api_football_id",
        "sofa_score_id",
        "statsbomb_id",
    ]

    for competition_id, home_team_id, away_team_id, utc_date, _ in groups:
        matches = (
            db.query(Match)
            .filter(
                Match.competition_id == competition_id,
                Match.home_team_id == home_team_id,
                Match.away_team_id == away_team_id,
                Match.utc_date == utc_date,
            )
            .order_by(Match.id)
            .all()
        )

        for field_name in unique_provider_fields:
            values = {
                getattr(match_row, field_name)
                for match_row in matches
                if getattr(match_row, field_name)
            }
            if len(values) > 1:
                summary.duplicate_match_conflict_groups += 1
                break

        # Match-level auto-merge is intentionally disabled.
        # In live data we found natural-key collisions with globally unique provider IDs,
        # so automatic collapse is not safe without a stricter business rule.
        continue


def derive_missing_values(db, summary: RepairSummary) -> None:
    matches = db.query(Match).all()
    for match in matches:
        if (
            match.winner is None
            and match.home_score is not None
            and match.away_score is not None
        ):
            if match.home_score > match.away_score:
                match.winner = "HOME_TEAM"
            elif match.away_score > match.home_score:
                match.winner = "AWAY_TEAM"
            else:
                match.winner = "DRAW"
            summary.winners_derived += 1

        lineup_rows = (
            db.query(MatchLineup).filter(MatchLineup.match_id == match.id).all()
        )
        for lineup in lineup_rows:
            if (
                lineup.team_id == match.home_team_id
                and not match.home_formation
                and lineup.formation
            ):
                match.home_formation = lineup.formation
                summary.formations_derived += 1
            elif (
                lineup.team_id == match.away_team_id
                and not match.away_formation
                and lineup.formation
            ):
                match.away_formation = lineup.formation
                summary.formations_derived += 1

        stats = (
            db.query(MatchStatistic).filter(MatchStatistic.match_id == match.id).first()
        )
        if stats:
            backfilled_this_match = False
            if match.home_possession is None and stats.home_possession is not None:
                match.home_possession = stats.home_possession
                backfilled_this_match = True
            if match.away_possession is None and stats.away_possession is not None:
                match.away_possession = stats.away_possession
                backfilled_this_match = True
            if (
                match.home_expected_goals is None
                and stats.home_expected_goals is not None
            ):
                match.home_expected_goals = stats.home_expected_goals
                backfilled_this_match = True
            if (
                match.away_expected_goals is None
                and stats.away_expected_goals is not None
            ):
                match.away_expected_goals = stats.away_expected_goals
                backfilled_this_match = True
            if backfilled_this_match:
                summary.match_stats_backfilled += 1

            if (
                stats.home_pass_accuracy is None
                and stats.home_passes
                and stats.home_successful_passes is not None
            ):
                stats.home_pass_accuracy = round(
                    (stats.home_successful_passes / max(stats.home_passes, 1)) * 100.0,
                    1,
                )
                summary.match_pass_accuracy_derived += 1
            if (
                stats.away_pass_accuracy is None
                and stats.away_passes
                and stats.away_successful_passes is not None
            ):
                stats.away_pass_accuracy = round(
                    (stats.away_successful_passes / max(stats.away_passes, 1)) * 100.0,
                    1,
                )
                summary.match_pass_accuracy_derived += 1

    performances = db.query(PlayerMatchPerformance).all()
    for perf in performances:
        if (
            perf.pass_accuracy is None
            and perf.passes
            and perf.successful_passes is not None
        ):
            perf.pass_accuracy = round(
                (perf.successful_passes / max(perf.passes, 1)) * 100.0, 1
            )
            summary.player_pass_accuracy_derived += 1
        if perf.player_id is None and perf.team_id and perf.player_name:
            player = (
                db.query(Player)
                .filter(
                    Player.team_id == perf.team_id,
                    func.lower(Player.name) == perf.player_name.strip().lower(),
                )
                .first()
            )
            if player:
                perf.player_id = player.id
                summary.player_links_filled += 1


def run_repairs(commit: bool) -> RepairSummary:
    summary = RepairSummary()
    db = SessionLocal()
    try:
        merge_duplicate_matches(db, summary)
        merge_duplicate_match_statistics(db, summary)
        merge_duplicate_lineups(db, summary)
        merge_duplicate_performances(db, summary)
        merge_duplicate_players(db, summary)
        derive_missing_values(db, summary)

        if commit:
            db.commit()
        else:
            db.rollback()
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def print_summary(summary: RepairSummary, committed: bool) -> None:
    print("=" * 100)
    print("DATA QUALITY REPAIR REPORT")
    print("=" * 100)
    for field_name, value in summary.__dict__.items():
        print(f"- {field_name.replace('_', ' ').title()}: {value}")
    print()
    print("Changes committed." if committed else "Dry run only. No changes committed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Repair duplicate or derivable data quality issues"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect and simulate repairs without committing changes",
    )
    args = parser.parse_args()

    result = run_repairs(commit=not args.dry_run)
    print_summary(result, committed=not args.dry_run)

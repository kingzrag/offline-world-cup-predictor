#!/usr/bin/env python3
"""
Database audit report for the production provider pipeline.

Reports:
- total competitions
- total international matches
- total players
- total player performances
- total match statistics
- total lineups
- total injuries
- total suspensions
- total xG records
- total passing records
- total goalkeeper records
- total interceptions
- total tackles
- total aerial duels
- per-column completeness for major tables

Writes a markdown report to DATABASE_AUDIT_REPORT.md by default.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text, and_, case, cast, func, or_

from database.connection import SessionLocal
from models import (
    Competition,
    Injury,
    Match,
    MatchEvent,
    MatchLineup,
    MatchStatistic,
    NationalTeamPlayer,
    Player,
    PlayerMatchPerformance,
    Standing,
    Suspension,
    Team,
)

INTERNATIONAL_CODES = {
    "WC",
    "EC",
    "CA",
    "UNL",
    "WWC",
    "OLY",
    "WCQ",
    "WCQA",
    "WCQC",
    "WCQE",
    "AFCON",
    "ASIAN",
    "CONCACAF",
    "GC",
}

INTERNATIONAL_NAME_PATTERNS = [
    "%World Cup%",
    "%Women%World Cup%",
    "%Euro%",
    "%European Championship%",
    "%Copa America%",
    "%Copa América%",
    "%Nations League%",
    "%Olympic%",
    "%Qualifying%",
    "%Africa Cup of Nations%",
    "%Asian Cup%",
    "%Gold Cup%",
]

TABLES = [
    Competition,
    Team,
    Player,
    Match,
    MatchStatistic,
    MatchLineup,
    MatchEvent,
    PlayerMatchPerformance,
    Injury,
    Suspension,
    NationalTeamPlayer,
    Standing,
]


def international_match_filter():
    name_filters = [
        Competition.name.ilike(pattern) for pattern in INTERNATIONAL_NAME_PATTERNS
    ]
    return or_(Competition.code.in_(INTERNATIONAL_CODES), *name_filters)


def is_string_like(column) -> bool:
    return isinstance(column.type, (String, Text, SAEnum))


def populated_condition(column):
    if is_string_like(column):
        return and_(
            column.is_not(None), func.length(func.trim(cast(column, String))) > 0
        )
    return column.is_not(None)


def pct(populated: int, total: int) -> float:
    if total <= 0:
        return 100.0
    return round((populated / total) * 100.0, 2)


def table_completeness(db, model) -> List[Dict[str, Any]]:
    total_rows = db.query(func.count()).select_from(model).scalar() or 0
    rows: List[Dict[str, Any]] = []
    for column in model.__table__.columns:
        populated_rows = (
            db.query(func.count())
            .select_from(model)
            .filter(populated_condition(column))
            .scalar()
            or 0
        )
        empty_rows = total_rows - populated_rows
        rows.append(
            {
                "column": column.name,
                "type": str(column.type),
                "populated_rows": int(populated_rows),
                "empty_rows": int(empty_rows),
                "percent_complete": pct(int(populated_rows), int(total_rows)),
            }
        )
    return rows


def fetch_totals(db) -> Dict[str, Any]:
    intl_match_count = (
        db.query(func.count(Match.id))
        .join(Competition, Competition.id == Match.competition_id)
        .filter(international_match_filter())
        .scalar()
        or 0
    )

    match_xg_records = (
        db.query(func.count(MatchStatistic.id))
        .filter(
            or_(
                MatchStatistic.home_expected_goals.is_not(None),
                MatchStatistic.away_expected_goals.is_not(None),
            )
        )
        .scalar()
        or 0
    )
    player_xg_records = (
        db.query(func.count(PlayerMatchPerformance.id))
        .filter(PlayerMatchPerformance.statsbomb_xg > 0)
        .scalar()
        or 0
    )

    match_passing_records = (
        db.query(func.count(MatchStatistic.id))
        .filter(
            or_(
                MatchStatistic.home_passes.is_not(None),
                MatchStatistic.away_passes.is_not(None),
                MatchStatistic.home_successful_passes.is_not(None),
                MatchStatistic.away_successful_passes.is_not(None),
                MatchStatistic.home_pass_accuracy.is_not(None),
                MatchStatistic.away_pass_accuracy.is_not(None),
            )
        )
        .scalar()
        or 0
    )
    player_passing_records = (
        db.query(func.count(PlayerMatchPerformance.id))
        .filter(
            or_(
                PlayerMatchPerformance.passes > 0,
                PlayerMatchPerformance.successful_passes > 0,
                PlayerMatchPerformance.pass_accuracy > 0,
            )
        )
        .scalar()
        or 0
    )

    goalkeeper_records = (
        db.query(func.count(PlayerMatchPerformance.id))
        .filter(
            or_(
                PlayerMatchPerformance.saves > 0,
                PlayerMatchPerformance.position.ilike("%GK%"),
                PlayerMatchPerformance.position.ilike("Goalkeeper%"),
            )
        )
        .scalar()
        or 0
    )

    match_interception_records = (
        db.query(func.count(MatchStatistic.id))
        .filter(
            or_(
                MatchStatistic.home_interceptions.is_not(None),
                MatchStatistic.away_interceptions.is_not(None),
            )
        )
        .scalar()
        or 0
    )
    player_interception_records = (
        db.query(func.count(PlayerMatchPerformance.id))
        .filter(PlayerMatchPerformance.interceptions > 0)
        .scalar()
        or 0
    )

    match_tackle_records = (
        db.query(func.count(MatchStatistic.id))
        .filter(
            or_(
                MatchStatistic.home_tackles.is_not(None),
                MatchStatistic.away_tackles.is_not(None),
            )
        )
        .scalar()
        or 0
    )
    player_tackle_records = (
        db.query(func.count(PlayerMatchPerformance.id))
        .filter(PlayerMatchPerformance.tackles > 0)
        .scalar()
        or 0
    )

    match_aerial_records = (
        db.query(func.count(MatchStatistic.id))
        .filter(
            or_(
                MatchStatistic.home_aerial_duels.is_not(None),
                MatchStatistic.away_aerial_duels.is_not(None),
            )
        )
        .scalar()
        or 0
    )
    player_aerial_records = (
        db.query(func.count(PlayerMatchPerformance.id))
        .filter(PlayerMatchPerformance.aerial_duels > 0)
        .scalar()
        or 0
    )

    return {
        "total_competitions": db.query(func.count(Competition.id)).scalar() or 0,
        "total_international_matches": intl_match_count,
        "total_players": db.query(func.count(Player.id)).scalar() or 0,
        "total_player_performances": db.query(
            func.count(PlayerMatchPerformance.id)
        ).scalar()
        or 0,
        "total_match_statistics": db.query(func.count(MatchStatistic.id)).scalar() or 0,
        "total_lineups": db.query(func.count(MatchLineup.id)).scalar() or 0,
        "total_injuries": db.query(func.count(Injury.id)).scalar() or 0,
        "total_suspensions": db.query(func.count(Suspension.id)).scalar() or 0,
        "total_xg_records": match_xg_records + player_xg_records,
        "total_xg_records_breakdown": {
            "match_statistics": match_xg_records,
            "player_performances": player_xg_records,
        },
        "total_passing_records": match_passing_records + player_passing_records,
        "total_passing_records_breakdown": {
            "match_statistics": match_passing_records,
            "player_performances": player_passing_records,
        },
        "total_goalkeeper_records": goalkeeper_records,
        "total_interceptions": match_interception_records + player_interception_records,
        "total_interceptions_breakdown": {
            "match_statistics": match_interception_records,
            "player_performances": player_interception_records,
        },
        "total_tackles": match_tackle_records + player_tackle_records,
        "total_tackles_breakdown": {
            "match_statistics": match_tackle_records,
            "player_performances": player_tackle_records,
        },
        "total_aerial_duels": match_aerial_records + player_aerial_records,
        "total_aerial_duels_breakdown": {
            "match_statistics": match_aerial_records,
            "player_performances": player_aerial_records,
        },
    }


def build_markdown_report(results: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Database Audit Report")
    lines.append("")
    lines.append(f"Generated: {results['generated_at']}")
    lines.append("")
    lines.append("## Required Totals")
    lines.append("")
    for key, value in results["totals"].items():
        if key.endswith("_breakdown"):
            continue
        label = key.replace("_", " ").title()
        lines.append(f"- **{label}**: {value:,}")
        breakdown = results["totals"].get(f"{key}_breakdown")
        if isinstance(breakdown, dict):
            for sub_key, sub_value in breakdown.items():
                lines.append(f"  - {sub_key.replace('_', ' ')}: {sub_value:,}")
    lines.append("")

    lines.append("## Column Completeness")
    lines.append("")
    for table_name, rows in results["completeness"].items():
        lines.append(f"### `{table_name}`")
        lines.append("")
        lines.append("| Column | Type | Populated Rows | Empty Rows | % Complete |")
        lines.append("|---|---:|---:|---:|---:|")
        for row in rows:
            lines.append(
                f"| `{row['column']}` | `{row['type']}` | {row['populated_rows']:,} | {row['empty_rows']:,} | {row['percent_complete']:.2f}% |"
            )
        lines.append("")
    return "\n".join(lines)


def run_audit(output_path: str) -> Tuple[Dict[str, Any], str]:
    db = SessionLocal()
    try:
        results = {
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            + "Z",
            "totals": fetch_totals(db),
            "completeness": {
                model.__tablename__: table_completeness(db, model) for model in TABLES
            },
        }
        markdown = build_markdown_report(results)
        Path(output_path).write_text(markdown, encoding="utf-8")
        return results, markdown
    finally:
        db.close()


def print_summary(results: Dict[str, Any], output_path: str) -> None:
    print("=" * 100)
    print("DATABASE AUDIT REPORT")
    print("=" * 100)
    for key, value in results["totals"].items():
        if key.endswith("_breakdown"):
            continue
        label = key.replace("_", " ").title()
        print(f"- {label}: {value:,}")
        breakdown = results["totals"].get(f"{key}_breakdown")
        if isinstance(breakdown, dict):
            for sub_key, sub_value in breakdown.items():
                print(f"    * {sub_key.replace('_', ' ')}: {sub_value:,}")
    print()
    print(f"Detailed markdown report written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a database audit for the provider pipeline"
    )
    parser.add_argument(
        "--output",
        default="DATABASE_AUDIT_REPORT.md",
        help="Markdown report path (default: DATABASE_AUDIT_REPORT.md)",
    )
    args = parser.parse_args()

    audit_results, _ = run_audit(args.output)
    print_summary(audit_results, args.output)

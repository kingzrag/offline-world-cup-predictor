#!/usr/bin/env python3
"""
Generate ENGINEERED_FEATURES_REPORT.md from real PostgreSQL data.

Coverage percentages are computed across finished international matches that have at
least one enrichment row in `match_statistics`, `player_match_performances`, or
`match_lineups`. A feature counts as available for a match only when both home and away
team values were backed by supporting inputs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import desc, func, or_

from database.connection import SessionLocal
from models import (
    Competition,
    Match,
    MatchLineup,
    MatchStatistic,
    PlayerMatchPerformance,
)
from services.intelligence_service import IntelligenceService

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

FEATURE_METADATA = {
    "goalkeeper_strength": {
        "formula": "0.35*gk_rating_score + 0.25*saves_score + 0.20*clean_sheet_rate + 0.20*conceded_score",
        "db_fields": [
            "player_match_performances.rating",
            "player_match_performances.sofa_score_rating",
            "player_match_performances.saves",
            "player_match_performances.position",
            "matches.home_score",
            "matches.away_score",
        ],
        "providers": ["StatsBomb", "SofaScore", "FootballData"],
    },
    "passing_strength": {
        "formula": "0.35*pass_accuracy + 0.20*passes_norm + 0.25*successful_passes_norm + 0.20*possession_norm",
        "db_fields": [
            "match_statistics.home_pass_accuracy",
            "match_statistics.away_pass_accuracy",
            "match_statistics.home_passes",
            "match_statistics.away_passes",
            "match_statistics.home_successful_passes",
            "match_statistics.away_successful_passes",
            "match_statistics.home_possession",
            "match_statistics.away_possession",
        ],
        "providers": ["StatsBomb", "FBref", "API-Football", "SofaScore"],
    },
    "recent_form": {
        "formula": "0.50*points_ratio + 0.25*goal_diff_score + 0.25*xg_diff_score over last 5 matches",
        "db_fields": [
            "matches.winner",
            "matches.home_score",
            "matches.away_score",
            "match_statistics.home_expected_goals",
            "match_statistics.away_expected_goals",
        ],
        "providers": ["FootballData", "StatsBomb", "SofaScore"],
    },
    "aerial_dominance": {
        "formula": "0.70*aerial_win_pct + 0.30*aerial_volume_norm",
        "db_fields": [
            "player_match_performances.aerial_duels",
            "player_match_performances.aerial_duels_won",
            "match_statistics.home_aerial_duels",
            "match_statistics.away_aerial_duels",
        ],
        "providers": ["StatsBomb", "FBref"],
    },
    "pressing_strength": {
        "formula": "0.30*tackles_norm + 0.25*interceptions_norm + 0.45*pressures_norm",
        "db_fields": [
            "match_statistics.home_tackles",
            "match_statistics.away_tackles",
            "match_statistics.home_interceptions",
            "match_statistics.away_interceptions",
            "match_statistics.home_pressures",
            "match_statistics.away_pressures",
            "player_match_performances.pressures",
        ],
        "providers": ["StatsBomb", "FBref"],
    },
    "defensive_stability": {
        "formula": "0.35*clean_sheet_rate + 0.30*inverse_xga + 0.25*inverse_goals_conceded + 0.10*blocks_norm",
        "db_fields": [
            "matches.home_score",
            "matches.away_score",
            "match_statistics.home_expected_goals",
            "match_statistics.away_expected_goals",
            "player_match_performances.blocks",
            "player_match_performances.clearances",
        ],
        "providers": ["FootballData", "StatsBomb", "FBref"],
    },
    "attacking_efficiency": {
        "formula": "0.30*xg_norm + 0.30*goals_norm + 0.20*shots_on_target_rate + 0.20*conversion_rate",
        "db_fields": [
            "matches.home_score",
            "matches.away_score",
            "match_statistics.home_expected_goals",
            "match_statistics.away_expected_goals",
            "match_statistics.home_shots",
            "match_statistics.away_shots",
            "match_statistics.home_shots_on_target",
            "match_statistics.away_shots_on_target",
        ],
        "providers": ["FootballData", "StatsBomb", "SofaScore"],
    },
    "finishing_quality": {
        "formula": "0.70*(goals/xG)_norm + 0.30*shots_on_target_rate; big chances are unavailable and omitted",
        "db_fields": [
            "matches.home_score",
            "matches.away_score",
            "match_statistics.home_expected_goals",
            "match_statistics.away_expected_goals",
            "match_statistics.home_shots",
            "match_statistics.away_shots",
            "match_statistics.home_shots_on_target",
            "match_statistics.away_shots_on_target",
        ],
        "providers": ["FootballData", "StatsBomb", "SofaScore"],
    },
    "set_piece_strength": {
        "formula": "0.55*corners_norm + 0.45*aerial_win_pct",
        "db_fields": [
            "match_statistics.home_corners",
            "match_statistics.away_corners",
            "player_match_performances.aerial_duels",
            "player_match_performances.aerial_duels_won",
        ],
        "providers": ["StatsBomb", "FBref"],
    },
    "midfield_control": {
        "formula": "0.40*pass_accuracy + 0.20*successful_passes_norm + 0.15*passes_norm + 0.25*possession_norm",
        "db_fields": [
            "match_statistics.home_pass_accuracy",
            "match_statistics.away_pass_accuracy",
            "match_statistics.home_successful_passes",
            "match_statistics.away_successful_passes",
            "match_statistics.home_passes",
            "match_statistics.away_passes",
            "match_statistics.home_possession",
            "match_statistics.away_possession",
        ],
        "providers": ["StatsBomb", "FBref", "API-Football", "SofaScore"],
    },
    "squad_availability": {
        "formula": "0.50*player_availability + 0.30*available_starters_ratio + 0.10*(1-injury_impact) + 0.10*(1-suspension_impact)",
        "db_fields": [
            "injuries.player_name",
            "injuries.player_market_value",
            "suspensions.player_name",
            "suspensions.player_market_value",
            "national_team_players.player_name",
            "national_team_players.market_value",
        ],
        "providers": ["Transfermarkt"],
    },
    "tactical_stability": {
        "formula": "0.55*formation_consistency + 0.45*lineup_consistency",
        "db_fields": [
            "match_lineups.formation",
            "match_lineups.starting_xi",
        ],
        "providers": ["StatsBomb", "SofaScore"],
    },
}


def enriched_international_matches(db, limit: int | None):
    query = (
        db.query(Match)
        .join(Competition, Competition.id == Match.competition_id)
        .outerjoin(MatchStatistic, MatchStatistic.match_id == Match.id)
        .outerjoin(PlayerMatchPerformance, PlayerMatchPerformance.match_id == Match.id)
        .outerjoin(MatchLineup, MatchLineup.match_id == Match.id)
        .filter(
            Match.status == "FINISHED",
            Competition.code.in_(INTERNATIONAL_CODES),
            or_(
                MatchStatistic.id.is_not(None),
                PlayerMatchPerformance.id.is_not(None),
                MatchLineup.id.is_not(None),
            ),
        )
        .group_by(Match.id)
        .order_by(desc(Match.utc_date))
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def compute_coverage(db, limit: int | None):
    svc = IntelligenceService()
    matches = enriched_international_matches(db, limit)
    counts = {feature_name: 0 for feature_name in FEATURE_METADATA}

    for match in matches:
        audit = svc.explain_engineered_features(db, match)
        for feature_name in FEATURE_METADATA:
            payload = audit["features"][feature_name]
            if payload["home"]["available"] and payload["away"]["available"]:
                counts[feature_name] += 1

    total = len(matches)
    percentages = {
        feature_name: round((count / total) * 100.0, 2) if total else 0.0
        for feature_name, count in counts.items()
    }
    return total, counts, percentages


def build_report(total_matches: int, counts: dict, percentages: dict) -> str:
    lines = []
    lines.append("# Engineered Features Report")
    lines.append("")
    lines.append(
        f"Generated: {datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}Z"
    )
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        f"Coverage below is measured across **{total_matches} finished international matches with enrichment data** "
        "(`match_statistics`, `player_match_performances`, or `match_lineups`)."
    )
    lines.append(
        "A feature is counted as available for a match only when **both home and away team values** had supporting inputs."
    )
    lines.append("")
    lines.append("## Engineered Feature Catalog")
    lines.append("")
    lines.append(
        "| Feature | Calculation formula | Database fields used | Providers contributing data | Matches available | Availability % |"
    )
    lines.append("|---|---|---|---|---:|---:|")

    for feature_name, meta in FEATURE_METADATA.items():
        lines.append(
            f"| `{feature_name}` | {meta['formula']} | "
            f"{', '.join(f'`{field}`' for field in meta['db_fields'])} | "
            f"{', '.join(meta['providers'])} | {counts[feature_name]} | {percentages[feature_name]:.2f}% |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- Existing intelligence fields remain unchanged and backward-compatible."
    )
    lines.append(
        "- These engineered features are internal ML features only; frontend behavior is unchanged."
    )
    lines.append(
        "- `midfield_control` already existed and was strengthened using pass volume + successful passes + possession."
    )
    lines.append(
        "- `goalkeeper_strength`, `passing_strength`, and `recent_form` extend existing metrics without removing `goalkeeper_performance`, `passing_dominance`, or `momentum_score`."
    )
    lines.append(
        "- `big chances scored` is not currently stored in PostgreSQL, so `finishing_quality` excludes it and relies on goals/xG + shot quality proxies."
    )
    lines.append(
        "- `recoveries` are not currently stored as a dedicated field, so `pressing_strength` uses tackles, interceptions, and pressures."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate ENGINEERED_FEATURES_REPORT.md"
    )
    parser.add_argument(
        "--limit", type=int, help="Optional limit on enriched matches to audit"
    )
    parser.add_argument(
        "--output",
        default="ENGINEERED_FEATURES_REPORT.md",
        help="Output markdown path relative to project root",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total_matches, counts, percentages = compute_coverage(db, args.limit)
        report = build_report(total_matches, counts, percentages)
        Path(args.output).write_text(report, encoding="utf-8")
        print(
            f"Wrote {args.output} using {total_matches} enriched international matches"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

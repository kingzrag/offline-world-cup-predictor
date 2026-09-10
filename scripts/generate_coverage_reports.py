#!/usr/bin/env python3
"""
scripts/generate_coverage_reports.py
=====================================
Generates two audit reports after the data pipeline:

  1. multi_source_coverage_report.md    — how many matches exist per competition
     per source, coverage years, and completeness gaps
  2. provider_capability_matrix.md      — what each live API provider can supply
     and verified capability status

Usage:
  python scripts/generate_coverage_reports.py

Output files written to: reports/ directory
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from utils.logger import logger


# Target competitions in exact order from Phase 2.5
TARGET_COMPETITIONS = [
    ("PL",   "Premier League",                 "DOMESTIC"),
    ("PD",   "La Liga",                        "DOMESTIC"),
    ("SA",   "Serie A",                        "DOMESTIC"),
    ("BL1",  "Bundesliga",                     "DOMESTIC"),
    ("FL1",  "Ligue 1",                        "DOMESTIC"),
    ("DED",  "Eredivisie",                     "DOMESTIC"),
    ("PPL",  "Primeira Liga",                  "DOMESTIC"),
    ("JPL",  "Belgian Pro League",             "DOMESTIC"),
    ("TSL",  "Türk Süper Lig",                "DOMESTIC"),
    ("MLS",  "MLS",                            "NORTH_AMERICA"),
    ("CL",   "Champions League",               "UEFA"),
    ("EL",   "Europa League",                  "UEFA"),
    ("UECL", "Conference League",              "UEFA"),
    ("WC",   "World Cup",                      "INTERNATIONAL"),
    ("WCQ",  "World Cup Qualifiers",           "INTERNATIONAL"),
    ("EC",   "European Championship",          "INTERNATIONAL"),
    ("EUQ",  "Euro Qualifiers",                "INTERNATIONAL"),
    ("UNL",  "Nations League",                 "INTERNATIONAL"),
    ("CA",   "Copa America",                   "INTERNATIONAL"),
    ("FRI",  "International Friendlies",       "INTERNATIONAL"),
]

SOURCES = [
    "schochastics",
    "footballcsv",
    "openfootball",
    "football_data_org",
    "thesportsdb",
    "api_football",
]

PROVIDER_CAPABILITIES = {
    "Football-Data.org": {
        "endpoint": "https://api.football-data.org/v4",
        "status": "OPERATIONAL",
        "free_tier": True,
        "competitions": ["PL", "BL1", "SA", "FL1", "PD", "DED", "PPL", "CL", "EC", "WC"],
        "historical_matches": "YES",
        "fixtures": "YES",
        "standings": "YES",
        "live_scores": "DELAYED (not real-time)",
        "lineups": "PREMIUM",
        "statistics": "PREMIUM",
        "injuries": "NO",
        "odds": "NO",
        "rate_limit": "10 req/min (free)",
        "notes": "Primary API for current season. Real-time not available on free plan.",
    },
    "TheSportsDB": {
        "endpoint": "https://www.thesportsdb.com/api/v1/json/123",
        "status": "OPERATIONAL (free tier)",
        "free_tier": True,
        "competitions": ["PL", "PD", "SA", "BL1", "FL1", "DED", "PPL", "CL", "EL", "WC", "EC", "MLS"],
        "historical_matches": "YES (eventsseason.php)",
        "fixtures": "YES (eventsnextleague.php)",
        "standings": "NO (not v1 free)",
        "live_scores": "PREMIUM ONLY (2-min updates)",
        "lineups": "NO",
        "statistics": "NO",
        "injuries": "NO",
        "odds": "NO",
        "rate_limit": "~30 req/min",
        "notes": "Free key=123 per official docs. Livescore NOT real-time on free tier.",
    },
    "API-Football": {
        "endpoint": "https://v3.football.api-sports.io",
        "status": "SUSPENDED (account error)",
        "free_tier": False,
        "competitions": ["N/A - account suspended"],
        "historical_matches": "UNAVAILABLE",
        "fixtures": "UNAVAILABLE",
        "standings": "UNAVAILABLE",
        "live_scores": "UNAVAILABLE",
        "lineups": "UNAVAILABLE",
        "statistics": "UNAVAILABLE",
        "injuries": "UNAVAILABLE",
        "odds": "UNAVAILABLE",
        "rate_limit": "N/A",
        "notes": "Account suspended as of 2026-09-08. Circuit-breaker enabled. DO NOT remove from codebase — may reactivate.",
    },
    "Schochastics (GitHub)": {
        "endpoint": "https://github.com/schochastics/football-data",
        "status": "OPERATIONAL (local parquet)",
        "free_tier": True,
        "competitions": ["All major European leagues + UEFA", "1888-2025"],
        "historical_matches": "YES (1.3M+ matches)",
        "fixtures": "NO",
        "standings": "NO",
        "live_scores": "NO",
        "lineups": "NO",
        "statistics": "NO",
        "injuries": "NO",
        "odds": "NO",
        "rate_limit": "N/A (local file)",
        "notes": "Best historical source. Priority 1.",
    },
    "OpenFootball (GitHub)": {
        "endpoint": "https://github.com/openfootball/champions-league",
        "status": "OPERATIONAL (local txt)",
        "free_tier": True,
        "competitions": ["CL", "EL", "ECL (2011-2026)"],
        "historical_matches": "YES",
        "fixtures": "YES (partial, 2025-26 has upcoming)",
        "standings": "NO",
        "live_scores": "NO",
        "lineups": "NO",
        "statistics": "NO",
        "injuries": "NO",
        "odds": "NO",
        "rate_limit": "N/A (local file)",
        "notes": "Priority 3 for UEFA competitions.",
    },
    "FootballCSV (GitHub)": {
        "endpoint": "https://github.com/footballcsv",
        "status": "OPERATIONAL (local CSV)",
        "free_tier": True,
        "competitions": ["England", "Italy", "France", "Belgium", "MLS", "CL"],
        "historical_matches": "YES",
        "fixtures": "NO",
        "standings": "NO",
        "live_scores": "NO",
        "lineups": "NO",
        "statistics": "NO",
        "injuries": "NO",
        "odds": "NO",
        "rate_limit": "N/A (local file)",
        "notes": "Priority 2. Good supplement for domestic leagues.",
    },
}


def query_coverage(db) -> dict:
    """Query DB for match coverage per competition."""
    from sqlalchemy import text
    coverage = {}

    for code, name, category in TARGET_COMPETITIONS:
        try:
            result = db.execute(text("""
                SELECT
                    COUNT(m.id)               AS match_count,
                    MIN(m.utc_date)::date     AS earliest,
                    MAX(m.utc_date)::date     AS latest,
                    COUNT(DISTINCT EXTRACT(YEAR FROM m.utc_date)) AS seasons
                FROM matches m
                JOIN competitions c ON c.id = m.competition_id
                WHERE c.code = :code
                  AND m.status = 'FINISHED'
            """), {"code": code}).fetchone()

            if result:
                coverage[code] = {
                    "name": name,
                    "category": category,
                    "match_count": result[0] or 0,
                    "earliest": str(result[1]) if result[1] else "N/A",
                    "latest": str(result[2]) if result[2] else "N/A",
                    "seasons": result[3] or 0,
                }
            else:
                coverage[code] = {
                    "name": name,
                    "category": category,
                    "match_count": 0,
                    "earliest": "N/A",
                    "latest": "N/A",
                    "seasons": 0,
                }
        except Exception as e:
            coverage[code] = {
                "name": name,
                "category": category,
                "match_count": 0,
                "earliest": "ERROR",
                "latest": "ERROR",
                "seasons": 0,
                "error": str(e),
            }

    return coverage


def query_freshness(db) -> list:
    """Query data_freshness table."""
    try:
        from sqlalchemy import text
        rows = db.execute(text("""
            SELECT provider, data_type, last_successful_update,
                   record_count, status, error_message, updated_at
            FROM data_freshness
            ORDER BY provider, data_type
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.warning(f"Could not query data_freshness: {e}")
        return []


def coverage_emoji(count: int) -> str:
    if count == 0:
        return "❌"
    if count < 50:
        return "⚠️"
    if count < 200:
        return "🟡"
    return "✅"


def generate_coverage_report(coverage: dict, freshness: list) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Multi-Source Competition Coverage Report",
        f"",
        f"Generated: {now}",
        "",
        "## Coverage by Competition",
        "",
        "| # | Competition | Category | Matches | Earliest | Latest | Seasons | Status |",
        "|---|-------------|----------|---------|----------|--------|---------|--------|",
    ]

    for i, (code, name, category) in enumerate(TARGET_COMPETITIONS, 1):
        d = coverage.get(code, {})
        count = d.get("match_count", 0)
        emoji = coverage_emoji(count)
        lines.append(
            f"| {i} | {name} (`{code}`) | {category} | {count:,} | "
            f"{d.get('earliest', 'N/A')} | {d.get('latest', 'N/A')} | "
            f"{d.get('seasons', 0)} | {emoji} |"
        )

    lines += [
        "",
        "### Status Legend",
        "- ✅ Good coverage (200+ finished matches)",
        "- 🟡 Partial coverage (50-199 matches)",
        "- ⚠️ Minimal coverage (<50 matches)",
        "- ❌ No data",
        "",
        "---",
        "",
        "## Data Freshness",
        "",
        "| Provider | Data Type | Last Updated | Records | Status |",
        "|----------|-----------|--------------|---------|--------|",
    ]

    for row in freshness:
        ts = row.get("last_successful_update")
        ts_str = str(ts)[:16] if ts else "Never"
        lines.append(
            f"| {row['provider']} | {row['data_type']} | {ts_str} | "
            f"{row.get('record_count', 0):,} | {row['status']} |"
        )

    if not freshness:
        lines.append("| (no records yet) | | | | |")

    return "\n".join(lines)


def generate_provider_matrix() -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Provider Capability Matrix",
        "",
        f"Generated: {now}",
        "",
        "> [!IMPORTANT]",
        "> API-Football account is currently SUSPENDED. The circuit-breaker is active.",
        "> TheSportsDB free tier does NOT provide real-time live scores.",
        "> Football-Data.org is the primary live data provider but updates are delayed.",
        "",
    ]

    for provider_name, caps in PROVIDER_CAPABILITIES.items():
        status = caps["status"]
        emoji = "✅" if "OPERATIONAL" in status else ("🔴" if "SUSPENDED" in status else "⚠️")
        lines.append(f"## {emoji} {provider_name}")
        lines.append("")
        lines.append(f"**Status:** `{status}`")
        lines.append(f"**Endpoint:** `{caps['endpoint']}`")
        lines.append(f"**Free Tier:** {'Yes' if caps['free_tier'] else 'No'}")
        lines.append("")
        lines.append("| Capability | Available |")
        lines.append("|-----------|-----------|")

        capability_keys = [
            "historical_matches", "fixtures", "standings",
            "live_scores", "lineups", "statistics", "injuries", "odds",
        ]
        for key in capability_keys:
            val = caps.get(key, "?")
            if val in ("YES", "OPERATIONAL"):
                icon = "✅"
            elif val in ("NO", "UNAVAILABLE"):
                icon = "❌"
            else:
                icon = "⚠️"
            lines.append(f"| {key.replace('_', ' ').title()} | {icon} {val} |")

        lines.append("")
        lines.append(f"**Rate Limit:** {caps.get('rate_limit', 'Unknown')}")
        lines.append(f"**Notes:** {caps.get('notes', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs("reports", exist_ok=True)

    db = next(get_db())
    try:
        coverage = query_coverage(db)
        freshness = query_freshness(db)
    finally:
        db.close()

    # Generate reports
    coverage_md = generate_coverage_report(coverage, freshness)
    provider_md = generate_provider_matrix()

    coverage_path = "reports/phase2_8_multi_source_coverage_report.md"
    provider_path = "reports/phase2_8_provider_capability_matrix.md"

    with open(coverage_path, "w") as f:
        f.write(coverage_md)
    with open(provider_path, "w") as f:
        f.write(provider_md)

    print(f"✅ Coverage report written: {coverage_path}")
    print(f"✅ Provider matrix written: {provider_path}")

    # Print summary
    print("\n=== COVERAGE SUMMARY ===")
    total = 0
    gaps = []
    for code, name, cat in TARGET_COMPETITIONS:
        count = coverage.get(code, {}).get("match_count", 0)
        total += count
        emoji = coverage_emoji(count)
        print(f"  {emoji} {name:35s} {count:>7,} matches")
        if count < 50:
            gaps.append(f"{name} ({code})")

    print(f"\n  TOTAL finished matches in DB: {total:,}")
    if gaps:
        print(f"\n⚠️  Coverage gaps (< 50 matches): {', '.join(gaps)}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    main()

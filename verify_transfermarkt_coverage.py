#!/usr/bin/env python3
"""
Verify Transfermarkt international-team injury/suspension coverage.

Reports:
- total international teams scanned
- successful pages
- failed pages
- skipped pages
- injuries collected
- suspensions collected
- coverage percentage
- parse failures
- cache hit rate
- detailed per-team breakdown
"""

from __future__ import annotations

import argparse
from typing import Dict, List, Tuple

from database.connection import SessionLocal
from providers.transfermarkt import (
    NATIONAL_TEAM_TRANSFERMARKT_URLS,
    TransfermarktProvider,
)
from services.transfermarkt_service import TransfermarktService


def unique_provider_teams() -> List[Tuple[str, str]]:
    seen_urls = set()
    teams: List[Tuple[str, str]] = []
    for team_name, url in sorted(NATIONAL_TEAM_TRANSFERMARKT_URLS.items()):
        if url in seen_urls:
            continue
        seen_urls.add(url)
        teams.append((team_name, url))
    return teams


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Transfermarkt scraping coverage"
    )
    parser.add_argument(
        "--competition", help="Optional competition code to limit to DB teams"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed per-team breakdown"
    )
    args = parser.parse_args()

    provider = TransfermarktProvider()
    db = SessionLocal()
    try:
        if args.competition:
            service = TransfermarktService()
            teams = []
            for team in service._competition_teams(db, args.competition):
                url = service._resolve_team_url(db, team)
                if url:
                    teams.append((team.name, url))
            deduped = []
            seen = set()
            for name, url in teams:
                if url in seen:
                    continue
                seen.add(url)
                deduped.append((name, url))
            team_rows = deduped
        else:
            team_rows = unique_provider_teams()

        totals: Dict[str, int] = {
            "teams_scanned": len(team_rows),
            "successful_pages": 0,
            "failed_pages": 0,
            "skipped_pages": 0,
            "injuries_collected": 0,
            "suspensions_collected": 0,
            "parse_failures": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "blocked_pages": 0,
            "empty_pages": 0,
        }
        failures = []
        team_details = []

        print("=" * 100)
        print("TRANSFERMARKT COVERAGE VERIFICATION")
        print("=" * 100)
        if args.competition:
            print(f"Competition filter: {args.competition}")
        print(f"Teams queued: {len(team_rows)}")
        print()

        for index, (team_name, url) in enumerate(team_rows, start=1):
            injuries, suspensions = provider._scrape_team_data(url)
            report = dict(provider.last_scrape_report)
            blocked = report.get("blocked", False)
            empty_page = report.get("empty_page", False)
            parse_failures = report.get("parse_failures", 0)
            from_cache = report.get("from_cache", False)
            players_extracted = report.get("players_extracted", 0)
            tables_seen = report.get("tables_seen", 0)
            candidate_tables = report.get("candidate_tables", 0)
            
            totals["parse_failures"] += parse_failures
            totals["injuries_collected"] += len(injuries)
            totals["suspensions_collected"] += len(suspensions)
            
            if from_cache:
                totals["cache_hits"] += 1
            else:
                totals["cache_misses"] += 1
            
            if blocked:
                totals["blocked_pages"] += 1
                totals["failed_pages"] += 1
                failures.append(
                    (team_name, report.get("error") or "blocked", url)
                )
                status = "BLOCKED"
            elif report.get("error") and not injuries and not suspensions:
                totals["failed_pages"] += 1
                failures.append(
                    (team_name, report.get("error") or "error", url)
                )
                status = "FAILED"
            elif empty_page and not injuries and not suspensions:
                totals["empty_pages"] += 1
                totals["skipped_pages"] += 1
                status = "EMPTY"
            else:
                totals["successful_pages"] += 1
                status = "OK"

            # Store detailed team information
            team_details.append({
                "team": team_name,
                "status": status,
                "players": players_extracted,
                "injuries": len(injuries),
                "suspensions": len(suspensions),
                "tables_seen": tables_seen,
                "candidate_tables": candidate_tables,
                "parse_failures": parse_failures,
                "from_cache": from_cache,
                "error": report.get("error"),
            })

            print(
                f"[{index:03d}/{len(team_rows):03d}] {status:6s} | team={team_name:25s} "
                f"players={players_extracted:3d} injuries={len(injuries):3d} "
                f"suspensions={len(suspensions):3d} tables={tables_seen:2d} candidates={candidate_tables:2d} "
                f"parse_failures={parse_failures:2d} cache={from_cache}"
            )

        scanned = max(totals["teams_scanned"], 1)
        coverage = (totals["successful_pages"] / scanned) * 100.0
        cache_hit_rate = (totals["cache_hits"] / max(totals["teams_scanned"], 1)) * 100.0

        print()
        print("-" * 100)
        print("SUMMARY")
        print("-" * 100)
        print(f"Total international teams scanned: {totals['teams_scanned']}")
        print(f"Successful pages:                 {totals['successful_pages']}")
        print(f"Failed pages:                     {totals['failed_pages']}")
        print(f"  - Blocked pages:                {totals['blocked_pages']}")
        print(f"  - Error pages:                  {totals['failed_pages'] - totals['blocked_pages']}")
        print(f"Skipped/empty pages:              {totals['skipped_pages']}")
        print(f"  - Empty pages:                 {totals['empty_pages']}")
        print(f"Injuries collected:               {totals['injuries_collected']}")
        print(f"Suspensions collected:            {totals['suspensions_collected']}")
        print(f"Parse failures:                   {totals['parse_failures']}")
        print(f"Cache performance:")
        print(f"  - Cache hits:                   {totals['cache_hits']}")
        print(f"  - Cache misses:                 {totals['cache_misses']}")
        print(f"  - Cache hit rate:               {cache_hit_rate:.2f}%")
        print(f"Coverage percentage:              {coverage:.2f}%")

        if failures:
            print()
            print("-" * 100)
            print("FAILED PAGES DETAILS")
            print("-" * 100)
            for team_name, reason, url in failures[:25]:
                print(f"- {team_name}: {reason}")
                print(f"  URL: {url}")
            if len(failures) > 25:
                print(f"... and {len(failures) - 25} more failures")

        if args.verbose:
            print()
            print("-" * 100)
            print("DETAILED TEAM BREAKDOWN")
            print("-" * 100)
            for detail in team_details:
                print(f"Team: {detail['team']}")
                print(f"  Status: {detail['status']}")
                print(f"  Players extracted: {detail['players']}")
                print(f"  Injuries: {detail['injuries']}")
                print(f"  Suspensions: {detail['suspensions']}")
                print(f"  Tables seen: {detail['tables_seen']}")
                print(f"  Candidate tables: {detail['candidate_tables']}")
                print(f"  Parse failures: {detail['parse_failures']}")
                print(f"  From cache: {detail['from_cache']}")
                if detail['error']:
                    print(f"  Error: {detail['error']}")
                print()

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

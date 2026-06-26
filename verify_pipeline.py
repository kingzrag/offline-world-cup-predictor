#!/usr/bin/env python3
"""
verify_pipeline.py — Full end-to-end pipeline verification

Runs the complete ingest_football_data() pipeline for a test competition
(defaults to WC) and verifies all steps complete without crashing.

Does NOT make permanent DB changes by default — use --write to persist.

Usage:
  python verify_pipeline.py                  # dry run (WC)
  python verify_pipeline.py --comp WC        # test specific competition
  python verify_pipeline.py --comp WC --write   # actually persist data
  python verify_pipeline.py --step fbref     # test only FBref step
"""

import asyncio
import argparse
import sys
import time
from datetime import datetime

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

def ok(msg):      print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):    print(f"  {RED}✗{RESET} {msg}")
def warn(msg):    print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg):    print(f"  {BLUE}→{RESET} {msg}")
def section(msg): print(f"\n{BLUE}{'='*60}{RESET}\n{BLUE}{msg}{RESET}\n{'='*60}")


async def run_full_pipeline(competition_code: str, write: bool, step_filter=None):
    from database.connection import SessionLocal
    from services.collection_service import CollectionService

    db = SessionLocal()
    svc = CollectionService()
    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        if step_filter:
            await run_single_step(db, svc, step_filter, competition_code, results)
        else:
            await run_all_steps(db, svc, competition_code, results)

        if write:
            db.commit()
            ok("Changes committed to database")
        else:
            db.rollback()
            info("Dry run — changes rolled back (use --write to persist)")

    except Exception as e:
        db.rollback()
        fail(f"Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
    finally:
        db.close()

    return results


async def run_single_step(db, svc, step: str, competition_code: str, results: dict):
    STEPS = {
        "fbref": ("FBref ingestion", svc.ingest_fbref_stats),
        "statsbomb": ("StatsBomb ingestion", svc.ingest_statsbomb_data),
        "api_football": ("API-Football ingestion", svc.ingest_api_football_data),
        "intelligence": ("Match Intelligence build", lambda db, cc: asyncio.coroutine(lambda: svc.build_match_intelligence(db, cc))()),
        "teams": ("Teams ingestion", svc.ingest_teams),
        "matches": ("Matches ingestion", svc.ingest_matches),
    }

    if step not in STEPS:
        fail(f"Unknown step '{step}'. Valid: {', '.join(STEPS.keys())}")
        results["failed"] += 1
        return

    label, fn = STEPS[step]
    section(f"Running: {label}")
    t0 = time.time()
    try:
        result = await fn(db, competition_code)
        elapsed = time.time() - t0
        ok(f"{label} completed in {elapsed:.1f}s")
        info(f"Result: {result}")
        results["passed"] += 1
    except Exception as e:
        fail(f"{label} failed: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1


async def run_all_steps(db, svc, competition_code: str, results: dict):
    section(f"Full Pipeline — {competition_code}")
    info(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    steps = [
        ("Step 1: Teams (Football-Data.org)", svc.ingest_teams),
        ("Step 2: Matches (Football-Data.org)", svc.ingest_matches),
        ("Step 3a: Injuries (Transfermarkt)", svc.ingest_injuries),
        ("Step 3b: Suspensions (Transfermarkt)", svc.ingest_suspensions),
        ("Step 3c: Players/Squad Values", svc.ingest_players),
    ]

    for label, fn in steps:
        info(f"\n{label}...")
        t0 = time.time()
        try:
            result = await fn(db, competition_code)
            elapsed = time.time() - t0
            ok(f"  Completed in {elapsed:.1f}s: {result}")
            results["passed"] += 1
        except Exception as e:
            fail(f"  Failed: {e}")
            results["failed"] += 1

    # FBref step
    info("\nStep 6: FBref Statistics...")
    t0 = time.time()
    try:
        result = await svc.ingest_fbref_stats(db, competition_code)
        elapsed = time.time() - t0
        status = result.get("status", "unknown")
        if status in ("success", "competition_not_supported", "provider_unavailable"):
            ok(f"  FBref completed in {elapsed:.1f}s: {status} — matches_updated={result.get('matches_updated', 0)}")
            results["passed"] += 1
        else:
            warn(f"  FBref status: {status}")
            results["warnings"] += 1
    except Exception as e:
        fail(f"  FBref failed: {e}")
        results["failed"] += 1

    # StatsBomb step
    info("\nStep 7: StatsBomb Open Data...")
    t0 = time.time()
    try:
        result = await svc.ingest_statsbomb_data(db, competition_code)
        elapsed = time.time() - t0
        status = result.get("status", "unknown")
        if status in ("success", "competition_not_in_open_data", "provider_unavailable"):
            ok(f"  StatsBomb completed in {elapsed:.1f}s: {status} — stats={result.get('stats_stored', 0)}, events={result.get('events_stored', 0)}")
            results["passed"] += 1
        else:
            warn(f"  StatsBomb status: {status}")
            results["warnings"] += 1
    except Exception as e:
        fail(f"  StatsBomb failed: {e}")
        results["failed"] += 1

    # API-Football step
    info("\nStep 8: API-Football...")
    t0 = time.time()
    try:
        result = await svc.ingest_api_football_data(db, competition_code)
        elapsed = time.time() - t0
        status = result.get("status", "unknown")
        if status in ("success", "disabled_no_key", "provider_unavailable"):
            ok(f"  API-Football completed in {elapsed:.1f}s: {status}")
            results["passed"] += 1
        else:
            warn(f"  API-Football status: {status}")
            results["warnings"] += 1
    except Exception as e:
        fail(f"  API-Football failed: {e}")
        results["failed"] += 1

    # Match Intelligence step
    info("\nStep 10: Match Intelligence...")
    t0 = time.time()
    try:
        result = svc.build_match_intelligence(db, competition_code)
        elapsed = time.time() - t0
        status = result.get("status", "unknown")
        if status in ("success", "competition_not_found"):
            ok(f"  Intelligence completed in {elapsed:.1f}s: {status} — matches_processed={result.get('matches_processed', 0)}")
            results["passed"] += 1
        else:
            warn(f"  Intelligence status: {status}, errors={result.get('errors', [])[:2]}")
            results["warnings"] += 1
    except Exception as e:
        fail(f"  Match Intelligence failed: {e}")
        results["failed"] += 1


async def check_provider_health():
    section("Provider Health Check")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    # Check FBref
    try:
        from providers.fbref import FBrefProvider
        p = FBrefProvider()
        ok("FBrefProvider: initialized")
        results["passed"] += 1
    except Exception as e:
        fail(f"FBrefProvider: {e}")
        results["failed"] += 1

    # Check StatsBomb
    try:
        from providers.statsbomb import StatsBombProvider
        p = StatsBombProvider()
        ok("StatsBombProvider: initialized")
        results["passed"] += 1
    except Exception as e:
        fail(f"StatsBombProvider: {e}")
        results["failed"] += 1

    # Check API-Football
    try:
        from providers.api_football import APIFootballProvider
        p = APIFootballProvider()
        if p.enabled:
            ok("APIFootballProvider: initialized + key present")
        else:
            warn("APIFootballProvider: initialized (no key — disabled)")
            results["warnings"] += 1
        results["passed"] += 1
    except Exception as e:
        fail(f"APIFootballProvider: {e}")
        results["failed"] += 1

    # Check IntelligenceService
    try:
        from services.intelligence_service import IntelligenceService
        svc = IntelligenceService()
        ok("IntelligenceService: initialized")
        results["passed"] += 1
    except Exception as e:
        fail(f"IntelligenceService: {e}")
        results["failed"] += 1

    # Check CollectionService
    try:
        from services.collection_service import CollectionService
        svc = CollectionService()
        ok(f"CollectionService: initialized (fbref={'✓' if svc.fbref_provider else '✗'}, "
           f"statsbomb={'✓' if svc.statsbomb_provider else '✗'}, "
           f"api_football={'✓' if svc.af_provider else '✗'})")
        results["passed"] += 1
    except Exception as e:
        fail(f"CollectionService: {e}")
        results["failed"] += 1

    return results


async def main():
    parser = argparse.ArgumentParser(description="Verify the full data collection pipeline")
    parser.add_argument("--comp", default="WC", help="Competition code to test (default: WC)")
    parser.add_argument("--write", action="store_true", help="Persist changes to DB (default: dry run)")
    parser.add_argument("--step", type=str, help="Run only a specific step (fbref, statsbomb, api_football, intelligence, teams, matches)")
    parser.add_argument("--health-only", action="store_true", help="Only check provider health, skip pipeline execution")
    args = parser.parse_args()

    health_results = await check_provider_health()
    
    if args.health_only:
        section("SUMMARY (health check only)")
        print(f"  {GREEN}Passed:   {health_results['passed']}{RESET}")
        print(f"  {YELLOW}Warnings: {health_results['warnings']}{RESET}")
        print(f"  {RED}Failed:   {health_results['failed']}{RESET}")
        sys.exit(0 if health_results["failed"] == 0 else 1)

    pipeline_results = await run_full_pipeline(args.comp, args.write, args.step)

    total_passed   = health_results["passed"]   + pipeline_results["passed"]
    total_failed   = health_results["failed"]   + pipeline_results["failed"]
    total_warnings = health_results["warnings"] + pipeline_results["warnings"]

    section("SUMMARY")
    print(f"  {GREEN}Passed:   {total_passed}{RESET}")
    print(f"  {YELLOW}Warnings: {total_warnings}{RESET}")
    print(f"  {RED}Failed:   {total_failed}{RESET}")

    if total_failed == 0:
        print(f"\n{GREEN}✓ Pipeline verification passed{'  (dry run — no DB changes)' if not args.write else ''}{RESET}")
    else:
        print(f"\n{RED}✗ {total_failed} failure(s) detected{RESET}")

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

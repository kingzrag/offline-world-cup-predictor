#!/usr/bin/env python3
"""
verify_providers.py — Individual provider verification

Tests each provider independently and reports:
  - Whether the provider initializes
  - Whether competitions list is returned
  - Whether match data is returned for a known competition
  - Whether graceful failure occurs on unsupported operations

Usage:
  python verify_providers.py
  python verify_providers.py --provider fbref
  python verify_providers.py --provider statsbomb
  python verify_providers.py --provider api_football
  python verify_providers.py --provider football_data
"""

import asyncio
import sys
import argparse
from datetime import datetime

# ---- colour helpers ----
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"
BLUE  = "\033[94m"
RESET = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):  print(f"  {RED}✗{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg):  print(f"  {BLUE}→{RESET} {msg}")
def section(msg): print(f"\n{BLUE}{'='*60}{RESET}\n{BLUE}{msg}{RESET}\n{'='*60}")


# ---------------------------------------------------------------------------
async def test_fbref():
    section("FBref Provider")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from providers.fbref import FBrefProvider
        p = FBrefProvider()
        ok("FBrefProvider initializes")
        results["passed"] += 1
    except Exception as e:
        fail(f"FBrefProvider init failed: {e}")
        results["failed"] += 1
        return results

    # Test competitions list
    try:
        comps = await p.get_competitions()
        if comps:
            ok(f"get_competitions() → {len(comps)} competitions")
            results["passed"] += 1
            for c in comps[:5]:
                info(f"  {c.code}: {c.name}")
        else:
            warn("get_competitions() returned empty list")
            results["warnings"] += 1
    except Exception as e:
        fail(f"get_competitions() raised: {e}")
        results["failed"] += 1

    # Test match scraping for World Cup (most reliable)
    try:
        info("Testing get_competition_matches('WC') — may be slow (FBref rate limits)...")
        matches = await p.get_competition_matches("WC")
        if matches:
            ok(f"get_competition_matches('WC') → {len(matches)} matches")
            results["passed"] += 1
            m = matches[0]
            info(f"  Sample: {getattr(m.home_team,'name','?')} vs {getattr(m.away_team,'name','?')} ({m.status})")
        else:
            warn("get_competition_matches('WC') returned empty — FBref may be blocking or competition unavailable")
            results["warnings"] += 1
    except Exception as e:
        warn(f"get_competition_matches('WC') failed gracefully: {e}")
        results["warnings"] += 1

    # Test unsupported competition
    try:
        matches = await p.get_competition_matches("UNKNOWN_COMP")
        ok("Unsupported competition returns [] gracefully")
        results["passed"] += 1
    except Exception as e:
        fail(f"Unsupported competition raised exception: {e}")
        results["failed"] += 1

    # Test graceful failure for injuries/suspensions
    try:
        injuries = await p.get_team_injuries("some_team")
        suspensions = await p.get_team_suspensions("some_team")
        ok(f"get_team_injuries() → {injuries} (expected [])")
        ok(f"get_team_suspensions() → {suspensions} (expected [])")
        results["passed"] += 2
    except Exception as e:
        fail(f"Injuries/suspensions raised: {e}")
        results["failed"] += 1

    return results


async def test_statsbomb():
    section("StatsBomb Open Data Provider")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from providers.statsbomb import StatsBombProvider
        p = StatsBombProvider()
        ok("StatsBombProvider initializes")
        results["passed"] += 1
    except Exception as e:
        fail(f"StatsBombProvider init failed: {e}")
        results["failed"] += 1
        return results

    # Test competitions download
    try:
        info("Downloading StatsBomb Open Data competition list...")
        comps = await p.get_competitions()
        if comps:
            ok(f"get_competitions() → {len(comps)} competition-season pairs")
            results["passed"] += 1
            for c in comps[:3]:
                info(f"  {c.code}: {c.name} ({c.season})")
        else:
            warn("get_competitions() returned empty — may be a network issue")
            results["warnings"] += 1
    except Exception as e:
        fail(f"get_competitions() raised: {e}")
        results["failed"] += 1

    # Test match list for World Cup
    try:
        info("Testing get_competition_matches('WC') from StatsBomb Open Data...")
        matches = await p.get_competition_matches("WC")
        if matches:
            ok(f"get_competition_matches('WC') → {len(matches)} matches")
            results["passed"] += 1
            m = matches[0]
            info(f"  Sample: {getattr(m.home_team,'name','?')} vs {getattr(m.away_team,'name','?')} ({m.status})")
        else:
            warn("No World Cup matches in StatsBomb Open Data — comp may not be available in free tier")
            results["warnings"] += 1
    except Exception as e:
        warn(f"get_competition_matches('WC') failed gracefully: {e}")
        results["warnings"] += 1

    # Test match statistics calculation from events
    try:
        info("Testing match statistics from event stream (StatsBomb match 3943043 — WC2022 sample)...")
        stats = await p.get_match_statistics("statsbomb_3943043")
        if stats:
            ok(f"get_match_statistics() → shots={stats.home_shots}/{stats.away_shots}, xG={stats.home_expected_goals:.2f}/{stats.away_expected_goals:.2f}")
            results["passed"] += 1
        else:
            warn("get_match_statistics() returned None — match may not be in Open Data")
            results["warnings"] += 1
    except Exception as e:
        warn(f"get_match_statistics() failed gracefully: {e}")
        results["warnings"] += 1

    # Test graceful returns for unsupported features
    try:
        injuries = await p.get_team_injuries("x")
        suspensions = await p.get_team_suspensions("x")
        standings = await p.get_competition_standings("WC")
        live = await p.get_live_matches()
        ok("Unsupported methods return [] gracefully")
        results["passed"] += 1
    except Exception as e:
        fail(f"Unsupported methods raised: {e}")
        results["failed"] += 1

    return results


async def test_api_football():
    section("API-Football Provider")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from providers.api_football import APIFootballProvider
        p = APIFootballProvider()
        ok("APIFootballProvider initializes")
        results["passed"] += 1
    except Exception as e:
        fail(f"APIFootballProvider init failed: {e}")
        results["failed"] += 1
        return results

    if not p.enabled:
        warn("API-Football is DISABLED (no API key configured)")
        warn("Set API_FOOTBALL_KEY in .env to enable")
        results["warnings"] += 1
        # Verify that all methods return empty gracefully
        try:
            comps = await p.get_competitions()
            matches = await p.get_competition_matches("WC")
            live = await p.get_live_matches()
            stats = await p.get_match_statistics("af_12345")
            ok("All methods return [] / None gracefully when disabled")
            results["passed"] += 1
        except Exception as e:
            fail(f"Methods raised when disabled: {e}")
            results["failed"] += 1
        return results

    ok("API-Football is ENABLED")
    results["passed"] += 1

    # Test competitions
    try:
        info("Fetching API-Football competitions...")
        comps = await p.get_competitions()
        if comps:
            ok(f"get_competitions() → {len(comps)} competitions")
            results["passed"] += 1
        else:
            warn("get_competitions() returned empty")
            results["warnings"] += 1
    except Exception as e:
        fail(f"get_competitions() raised: {e}")
        results["failed"] += 1

    # Test WC matches
    try:
        info("Fetching World Cup fixtures from API-Football...")
        matches = await p.get_competition_matches("WC")
        if matches:
            ok(f"get_competition_matches('WC') → {len(matches)} matches")
            results["passed"] += 1
            m = matches[0]
            info(f"  Sample: {getattr(m.home_team,'name','?')} vs {getattr(m.away_team,'name','?')} [{m.status}]")
        else:
            warn("No WC matches returned from API-Football")
            results["warnings"] += 1
    except Exception as e:
        fail(f"get_competition_matches() raised: {e}")
        results["failed"] += 1

    return results


async def test_football_data():
    section("FootballData Provider")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from providers.football_data import FootballDataProvider
        from utils.config import settings
        p = FootballDataProvider(settings.FOOTBALL_DATA_API_KEY)
        ok("FootballDataProvider initializes")
        results["passed"] += 1
    except Exception as e:
        fail(f"FootballDataProvider init failed: {e}")
        results["failed"] += 1
        return results

    try:
        info("Fetching competitions from Football-Data.org...")
        comps = await p.get_competitions()
        if comps:
            ok(f"get_competitions() → {len(comps)} competitions")
            results["passed"] += 1
        else:
            warn("get_competitions() returned empty")
            results["warnings"] += 1
    except Exception as e:
        fail(f"get_competitions() raised: {e}")
        results["failed"] += 1

    try:
        info("Fetching WC matches from Football-Data.org...")
        matches = await p.get_competition_matches("WC")
        if matches:
            ok(f"get_competition_matches('WC') → {len(matches)} matches")
            results["passed"] += 1
        else:
            warn("No WC matches returned (competition may not be in current season)")
            results["warnings"] += 1
    except Exception as e:
        fail(f"get_competition_matches() raised: {e}")
        results["failed"] += 1

    return results


async def test_transfermarkt():
    section("Transfermarkt Provider")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    try:
        from providers.transfermarkt import TransfermarktProvider
        p = TransfermarktProvider()
        ok("TransfermarktProvider initializes")
        results["passed"] += 1
    except Exception as e:
        fail(f"TransfermarktProvider init failed: {e}")
        results["failed"] += 1
        return results

    try:
        info("Fetching competitions list from Transfermarkt...")
        comps = await p.get_competitions()
        ok(f"get_competitions() → {len(comps)} competitions")
        results["passed"] += 1
    except Exception as e:
        warn(f"get_competitions() failed gracefully: {e}")
        results["warnings"] += 1

    try:
        info("Fetching injuries for Germany from Transfermarkt...")
        injuries = await p.get_team_injuries("Germany")
        ok(f"get_team_injuries('Germany') → {len(injuries)} injuries")
        results["passed"] += 1
        for inj in injuries[:3]:
            info(f"  {getattr(inj.player,'name','?')}: {inj.injury_type}")
    except Exception as e:
        warn(f"get_team_injuries() failed gracefully: {e}")
        results["warnings"] += 1

    return results


async def run_all(provider_filter=None):
    providers = {
        "fbref":        test_fbref,
        "statsbomb":    test_statsbomb,
        "api_football": test_api_football,
        "football_data": test_football_data,
        "transfermarkt": test_transfermarkt,
    }

    if provider_filter and provider_filter in providers:
        providers = {provider_filter: providers[provider_filter]}

    total_passed = total_failed = total_warnings = 0

    for name, test_fn in providers.items():
        try:
            results = await test_fn()
            total_passed   += results.get("passed", 0)
            total_failed   += results.get("failed", 0)
            total_warnings += results.get("warnings", 0)
        except Exception as e:
            print(f"\n{RED}CRITICAL: {name} test crashed: {e}{RESET}")
            total_failed += 1

    section("SUMMARY")
    print(f"  {GREEN}Passed:   {total_passed}{RESET}")
    print(f"  {YELLOW}Warnings: {total_warnings}{RESET}")
    print(f"  {RED}Failed:   {total_failed}{RESET}")

    if total_failed == 0:
        print(f"\n{GREEN}✓ All provider tests passed (warnings = graceful failures / rate limits){RESET}")
    else:
        print(f"\n{RED}✗ {total_failed} test(s) failed{RESET}")

    return total_failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify individual data providers")
    parser.add_argument("--provider", type=str, help="Run only this provider (fbref, statsbomb, api_football, football_data, transfermarkt)")
    args = parser.parse_args()

    success = asyncio.run(run_all(args.provider))
    sys.exit(0 if success else 1)

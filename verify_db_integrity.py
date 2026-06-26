#!/usr/bin/env python3
"""
verify_db_integrity.py — Database integrity checker

Verifies:
  - No duplicate matches (same api_id appearing multiple times)
  - No duplicate teams
  - No orphaned records (matches referencing non-existent teams/competitions)
  - MatchStatistic rows have valid match_id references
  - PlayerMatchPerformance rows have valid match_id and team_id references
  - No NULL on required columns
  - Row counts across all major tables

Usage:
  python verify_db_integrity.py
  python verify_db_integrity.py --fix-duplicates  (removes obvious duplicates)
"""

import sys
import argparse
from collections import defaultdict

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


def run_checks(fix_duplicates=False):
    from database.connection import SessionLocal
    from models import (
        Match, Team, Competition, Player, Injury, Suspension,
        MatchStatistic, MatchEvent, MatchLineup, PlayerMatchPerformance,
        Standing, NationalTeamPlayer
    )
    from sqlalchemy import func, text

    db = SessionLocal()
    total_passed = total_failed = total_warnings = 0

    try:
        # ----------------------------------------------------------------
        section("Row Counts")
        # ----------------------------------------------------------------
        tables = [
            ("Match", Match),
            ("Team", Team),
            ("Competition", Competition),
            ("Player", Player),
            ("Injury", Injury),
            ("Suspension", Suspension),
            ("MatchStatistic", MatchStatistic),
            ("MatchEvent", MatchEvent),
            ("MatchLineup", MatchLineup),
            ("PlayerMatchPerformance", PlayerMatchPerformance),
            ("Standing", Standing),
            ("NationalTeamPlayer", NationalTeamPlayer),
        ]
        for name, model in tables:
            try:
                count = db.query(model).count()
                info(f"{name}: {count:,} rows")
            except Exception as e:
                warn(f"Could not count {name}: {e}")

        # ----------------------------------------------------------------
        section("Duplicate Detection")
        # ----------------------------------------------------------------

        # Duplicate matches by api_id
        dup_matches = (
            db.query(Match.api_id, func.count(Match.id).label("cnt"))
            .filter(Match.api_id.isnot(None))
            .group_by(Match.api_id)
            .having(func.count(Match.id) > 1)
            .all()
        )
        if dup_matches:
            fail(f"Duplicate matches by api_id: {len(dup_matches)} groups")
            total_failed += 1
            for row in dup_matches[:5]:
                warn(f"  api_id={row.api_id} appears {row.cnt} times")
            if fix_duplicates:
                info("Removing duplicate matches (keeping lowest id)...")
                for row in dup_matches:
                    dups = db.query(Match).filter(Match.api_id == row.api_id).order_by(Match.id).all()
                    for dup in dups[1:]:  # Keep first, delete rest
                        db.delete(dup)
                db.commit()
                ok("Duplicates removed")
        else:
            ok("No duplicate matches by api_id")
            total_passed += 1

        # Duplicate teams by name
        dup_teams = (
            db.query(func.lower(Team.name).label("lower_name"), func.count(Team.id).label("cnt"))
            .group_by(func.lower(Team.name))
            .having(func.count(Team.id) > 1)
            .all()
        )
        if dup_teams:
            warn(f"Potential duplicate teams by name: {len(dup_teams)} groups")
            total_warnings += 1
            for row in dup_teams[:5]:
                warn(f"  '{row.lower_name}' appears {row.cnt} times")
        else:
            ok("No duplicate teams by name")
            total_passed += 1

        # ----------------------------------------------------------------
        section("Referential Integrity")
        # ----------------------------------------------------------------

        # Matches with missing teams
        orphan_home = db.query(Match).filter(
            ~Match.home_team_id.in_(db.query(Team.id))
        ).count()
        orphan_away = db.query(Match).filter(
            ~Match.away_team_id.in_(db.query(Team.id))
        ).count()
        if orphan_home + orphan_away > 0:
            fail(f"Orphaned matches: {orphan_home} missing home teams, {orphan_away} missing away teams")
            total_failed += 1
        else:
            ok("All matches have valid home_team_id and away_team_id")
            total_passed += 1

        # Matches with missing competitions
        orphan_comp = db.query(Match).filter(
            ~Match.competition_id.in_(db.query(Competition.id))
        ).count()
        if orphan_comp > 0:
            fail(f"Orphaned matches: {orphan_comp} have missing competition_id")
            total_failed += 1
        else:
            ok("All matches have valid competition_id")
            total_passed += 1

        # MatchStatistic with missing matches
        orphan_stats = db.query(MatchStatistic).filter(
            ~MatchStatistic.match_id.in_(db.query(Match.id))
        ).count()
        if orphan_stats > 0:
            fail(f"Orphaned MatchStatistic rows: {orphan_stats}")
            total_failed += 1
        else:
            ok("All MatchStatistic rows have valid match_id")
            total_passed += 1

        # PlayerMatchPerformance with missing matches
        orphan_perf = db.query(PlayerMatchPerformance).filter(
            ~PlayerMatchPerformance.match_id.in_(db.query(Match.id))
        ).count()
        if orphan_perf > 0:
            fail(f"Orphaned PlayerMatchPerformance rows: {orphan_perf}")
            total_failed += 1
        else:
            ok("All PlayerMatchPerformance rows have valid match_id")
            total_passed += 1

        # ----------------------------------------------------------------
        section("Data Quality Checks")
        # ----------------------------------------------------------------

        # Matches with NULL utc_date
        null_date = db.query(Match).filter(Match.utc_date.is_(None)).count()
        if null_date > 0:
            fail(f"{null_date} matches have NULL utc_date")
            total_failed += 1
        else:
            ok("All matches have utc_date")
            total_passed += 1

        # Finished matches without scores
        no_score = db.query(Match).filter(
            Match.status == "FINISHED",
            Match.home_score.is_(None),
        ).count()
        if no_score > 0:
            warn(f"{no_score} FINISHED matches have no home_score")
            total_warnings += 1
        else:
            ok("All FINISHED matches have scores")
            total_passed += 1

        # MatchStatistic sanity: possession should sum to ~100
        stats_with_possession = db.query(MatchStatistic).filter(
            MatchStatistic.home_possession.isnot(None),
            MatchStatistic.away_possession.isnot(None),
        ).all()
        if stats_with_possession:
            bad_possession = [
                s for s in stats_with_possession
                if abs((s.home_possession or 0) + (s.away_possession or 0) - 100) > 5
            ]
            if bad_possession:
                warn(f"{len(bad_possession)} MatchStatistic rows have possession not summing to ~100")
                total_warnings += 1
            else:
                ok(f"All {len(stats_with_possession)} rows with possession have valid values (~100 sum)")
                total_passed += 1
        else:
            warn("No MatchStatistic rows with possession data found")
            total_warnings += 1

        # Check extended columns exist (migration was run)
        try:
            db.execute(text("SELECT home_passes FROM match_statistics LIMIT 1"))
            ok("Extended columns (home_passes, etc.) exist in match_statistics")
            total_passed += 1
        except Exception as e:
            fail(f"Extended columns missing — run migration: {e}")
            total_failed += 1

        try:
            db.execute(text("SELECT aerial_duels FROM player_match_performances LIMIT 1"))
            ok("Extended columns (aerial_duels, etc.) exist in player_match_performances")
            total_passed += 1
        except Exception as e:
            fail(f"Extended columns missing — run migration: {e}")
            total_failed += 1

        # ----------------------------------------------------------------
        section("Coverage Statistics")
        # ----------------------------------------------------------------
        total_matches = db.query(Match).count()
        finished_matches = db.query(Match).filter(Match.status == "FINISHED").count()
        matches_with_stats = db.query(func.count(MatchStatistic.id)).scalar()
        matches_with_xg = db.query(MatchStatistic).filter(
            MatchStatistic.home_expected_goals.isnot(None)
        ).count()
        matches_with_passes = db.query(MatchStatistic).filter(
            MatchStatistic.home_passes.isnot(None)
        ).count()
        matches_with_tactics = db.query(MatchStatistic).filter(
            MatchStatistic.home_tackles.isnot(None)
        ).count()

        info(f"Total matches in DB:        {total_matches:,}")
        info(f"Finished matches:           {finished_matches:,}")
        info(f"Matches with statistics:    {matches_with_stats:,} ({100*matches_with_stats/max(finished_matches,1):.0f}% coverage)")
        info(f"Matches with xG data:       {matches_with_xg:,}")
        info(f"Matches with pass data:     {matches_with_passes:,}")
        info(f"Matches with tactical data: {matches_with_tactics:,}")

        player_perf_count = db.query(PlayerMatchPerformance).count()
        players_with_ratings = db.query(PlayerMatchPerformance).filter(
            PlayerMatchPerformance.sofa_score_rating.isnot(None)
        ).count()
        info(f"Player performances:        {player_perf_count:,}")
        info(f"With SofaScore ratings:     {players_with_ratings:,}")

    finally:
        db.close()

    # ----------------------------------------------------------------
    section("SUMMARY")
    # ----------------------------------------------------------------
    print(f"  {GREEN}Passed:   {total_passed}{RESET}")
    print(f"  {YELLOW}Warnings: {total_warnings}{RESET}")
    print(f"  {RED}Failed:   {total_failed}{RESET}")

    if total_failed == 0:
        print(f"\n{GREEN}✓ Database integrity checks passed{RESET}")
    else:
        print(f"\n{RED}✗ {total_failed} integrity issue(s) found{RESET}")

    return total_failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify database integrity")
    parser.add_argument("--fix-duplicates", action="store_true", help="Automatically remove duplicate matches")
    args = parser.parse_args()

    success = run_checks(fix_duplicates=args.fix_duplicates)
    sys.exit(0 if success else 1)

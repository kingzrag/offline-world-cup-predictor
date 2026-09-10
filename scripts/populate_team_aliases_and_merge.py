#!/usr/bin/env python3
"""
scripts/populate_team_aliases_and_merge.py
==========================================
1. Merges duplicate/stub teams safely using direct atomic SQL updates.
2. Populates the `team_aliases` table with official mappings from Football-Data, API-Football, and Transfermarkt.
"""

import sys, os
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import text
from database.connection import SessionLocal
from models import Team, TeamAlias
from ml.team_name_mappings import TEAM_NAME_MAP

def run_team_cleanup():
    db = SessionLocal()
    print("=" * 80)
    print("STEP 1: CANONICAL TEAM CLEANUP & ALIAS POPULATION")
    print("=" * 80)

    # 1. Merge duplicates
    stubs_to_merge = [
        ("Bayern Munich", "FC Bayern München"),
        ("Inter Milan", "FC Internazionale Milano"),
    ]

    print("\n--- 1. MERGE PLAN & EXECUTION ---")
    for stub_name, canon_name in stubs_to_merge:
        stub = db.query(Team).filter_by(name=stub_name).first()
        canon = db.query(Team).filter_by(name=canon_name).first()

        if not stub:
            print(f"  [SKIPPED] Stub '{stub_name}' does not exist in DB.")
            continue
        if not canon:
            print(f"  [WARNING] Canonical team '{canon_name}' does not exist. Renaming stub instead.")
            stub.name = canon_name
            db.commit()
            continue

        stub_id = stub.id
        canon_id = canon.id
        print(f"\nProcessing Merge: '{stub.name}' (ID {stub_id}) -> '{canon.name}' (ID {canon_id})")

        # Direct SQL Updates for all referencing tables
        tables_to_update = [
            ("matches", "home_team_id"),
            ("matches", "away_team_id"),
            ("standings", "team_id"),
            ("injuries", "team_id"),
            ("suspensions", "team_id"),
            ("players", "team_id"),
            ("match_lineups", "team_id"),
            ("player_match_performances", "team_id"),
            ("match_events", "team_id"),
            ("national_team_players", "team_id"),
            ("national_team_injuries", "team_id"),
            ("national_team_suspensions", "team_id"),
        ]

        for tbl, col in tables_to_update:
            try:
                res = db.execute(text(f"UPDATE {tbl} SET {col} = :canon_id WHERE {col} = :stub_id"), {"canon_id": canon_id, "stub_id": stub_id})
                if res.rowcount > 0:
                    print(f"  Updated {res.rowcount} rows in table '{tbl}' (column '{col}')")
            except Exception as e:
                print(f"  Note on '{tbl}.{col}': {e}")

        # Update team_name in text-based tables if needed
        db.execute(text("UPDATE injuries SET team_name = :canon_name WHERE team_name = :stub_name"), {"canon_name": canon.name, "stub_name": stub_name})
        db.execute(text("UPDATE suspensions SET team_name = :canon_name WHERE team_name = :stub_name"), {"canon_name": canon.name, "stub_name": stub_name})

        # Record alias
        existing_alias = db.query(TeamAlias).filter_by(provider="manual_cleanup", raw_name=stub_name).first()
        if not existing_alias:
            db.add(TeamAlias(
                provider="manual_cleanup",
                provider_team_id=str(stub.api_id) if stub.api_id else None,
                raw_name=stub_name,
                canonical_team_id=canon_id,
                canonical_name=canon.name,
                confidence=1.0
            ))

        # Delete stub safely
        db.execute(text("DELETE FROM teams WHERE id = :stub_id"), {"stub_id": stub_id})
        db.commit()
        print(f"  Successfully merged and deleted stub ID {stub_id}.")

    # 2. Populate team_aliases from TEAM_NAME_MAP
    print("\n--- 2. POPULATING team_aliases FROM TEAM_NAME_MAP ---")
    alias_count = 0
    skipped_count = 0

    for raw_name, canon_name in TEAM_NAME_MAP.items():
        canon = db.query(Team).filter(Team.name == canon_name).first()
        if not canon:
            clean = canon_name.lower().replace(" fc", "").replace(" cf", "").strip()
            canon = db.query(Team).filter(Team.name.ilike(f"%{clean}%")).first()

        if canon:
            existing = db.query(TeamAlias).filter_by(
                provider="football_data",
                raw_name=raw_name,
                canonical_team_id=canon.id
            ).first()
            if not existing:
                db.add(TeamAlias(
                    provider="football_data",
                    provider_team_id=str(canon.api_id) if canon.api_id else None,
                    raw_name=raw_name,
                    canonical_team_id=canon.id,
                    canonical_name=canon.name,
                    confidence=1.0
                ))
                alias_count += 1
        else:
            skipped_count += 1

    # Also add canonical self-aliases for all teams in DB
    all_teams = db.query(Team).all()
    self_alias_count = 0
    for t in all_teams:
        for provider in ["canonical", "api_football", "transfermarkt"]:
            existing = db.query(TeamAlias).filter_by(
                provider=provider,
                raw_name=t.name,
                canonical_team_id=t.id
            ).first()
            if not existing:
                db.add(TeamAlias(
                    provider=provider,
                    provider_team_id=str(t.api_id) if t.api_id else None,
                    raw_name=t.name,
                    canonical_team_id=t.id,
                    canonical_name=t.name,
                    confidence=1.0
                ))
                self_alias_count += 1

        if t.short_name and t.short_name != "None":
            existing = db.query(TeamAlias).filter_by(
                provider="short_name",
                raw_name=t.short_name,
                canonical_team_id=t.id
            ).first()
            if not existing:
                db.add(TeamAlias(
                    provider="short_name",
                    provider_team_id=str(t.api_id) if t.api_id else None,
                    raw_name=t.short_name,
                    canonical_team_id=t.id,
                    canonical_name=t.name,
                    confidence=1.0
                ))
                self_alias_count += 1

    db.commit()
    total_aliases = db.query(TeamAlias).count()
    print(f"Added {alias_count} football-data aliases, {self_alias_count} canonical/short aliases.")
    print(f"Total entries in team_aliases table: {total_aliases}")

    db.close()

if __name__ == '__main__':
    run_team_cleanup()

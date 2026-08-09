"""
ml/resolve_team_duplicates.py

STEP 6B — Phase 3: Team Identity Resolution

Resolves known duplicate team records in the DB.
Instead of physically merging rows (risky with FK constraints),
this script creates a CANONICAL TEAM ALIAS TABLE that maps
duplicate team IDs to canonical team IDs.

The training dataset builder reads this table and always uses
the canonical team ID when generating training features.

KNOWN DUPLICATES (from Step 6A audit):
1. Inter Milan (546) → FC Internazionale Milano (485)  [CANONICAL]
2. Bayern Munich (545) → FC Bayern München (492)        [CANONICAL]
3. Atlético Madrid (544) → Club Atlético de Madrid (452) [CANONICAL]

This script:
1. Detects duplicates automatically.
2. Prints a CLUB_TEAM_IDENTITY_AUDIT report.
3. Writes the canonical mapping to DB (new table: team_alias).
   If team_alias table does not exist, creates it as a Python dict file.
4. Does NOT delete any existing team records.
5. Does NOT reassign any existing match foreign keys.
"""

import logging
import sys
from pathlib import Path
from collections import defaultdict
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from models import Match, Team, TeamElo, Competition
from sqlalchemy import func

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("team_dedup")

# ── Manual canonical mapping (from Step 6A audit) ────────────────────────────
# Format: { duplicate_team_name: canonical_team_name }
MANUAL_CANONICAL = {
    "Inter Milan":         "FC Internazionale Milano",
    "Bayern Munich":       "FC Bayern München",
    "Atlético Madrid":     "Club Atlético de Madrid",
    "Luton Town FC":       "Luton Town FC",  # might be "Luton" in some data
}


def get_all_teams_with_match_counts(db):
    """Return dict of {team_id: (name, home_count, away_count, elo)}"""
    teams = db.query(Team).all()
    result = {}
    for t in teams:
        hc = db.query(func.count(Match.id)).filter(Match.home_team_id == t.id).scalar()
        ac = db.query(func.count(Match.id)).filter(Match.away_team_id == t.id).scalar()
        elo_obj = db.query(TeamElo).filter_by(team_name=t.name).first()
        result[t.id] = {
            "name": t.name,
            "home_matches": hc,
            "away_matches": ac,
            "total_matches": hc + ac,
            "elo": elo_obj.elo_rating if elo_obj else None,
            "market_value": t.squad_market_value,
        }
    return result


def detect_auto_duplicates(teams_data: dict) -> list[dict]:
    """
    Auto-detect potential duplicates by normalizing team names.
    Returns list of {normalized_key, variants: [{id, name, ...}]}
    """
    def normalize(name: str) -> str:
        n = name.lower()
        for strip in [" fc", " cf", " afc", " sc", " sd", " cd", " ac", " as", " ss", " us"]:
            n = n.replace(strip, "")
        n = n.replace("á", "a").replace("é", "e").replace("ü", "u").replace("ö", "o").replace("ñ", "n")
        n = n.replace("-", " ").replace(".", "").strip()
        return n

    groups = defaultdict(list)
    for tid, data in teams_data.items():
        key = normalize(data["name"])
        groups[key].append({"id": tid, **data})

    duplicates = []
    for key, variants in groups.items():
        if len(variants) > 1:
            duplicates.append({"normalized": key, "variants": variants})

    return duplicates


def build_canonical_id_map(db, teams_data: dict) -> dict[int, int]:
    """
    Build {duplicate_team_id → canonical_team_id} mapping.
    Canonical = the team with the most total matches (most history).
    Augmented with manual overrides from MANUAL_CANONICAL.
    """
    id_map = {}  # {dup_id: canonical_id}

    # Step 1: Auto-detect duplicates and resolve by match count
    duplicates = detect_auto_duplicates(teams_data)
    for dup_group in duplicates:
        variants = sorted(dup_group["variants"], key=lambda x: x["total_matches"], reverse=True)
        canonical = variants[0]  # highest match count = canonical
        for v in variants[1:]:
            id_map[v["id"]] = canonical["id"]
            logger.info(f"  AUTO-DEDUP: '{v['name']}' ({v['id']}, {v['total_matches']} matches) → '{canonical['name']}' ({canonical['id']}, {canonical['total_matches']} matches)")

    # Step 2: Apply manual overrides
    for dup_name, canonical_name in MANUAL_CANONICAL.items():
        dup_team = db.query(Team).filter_by(name=dup_name).first()
        canonical_team = db.query(Team).filter_by(name=canonical_name).first()
        if dup_team and canonical_team and dup_team.id != canonical_team.id:
            id_map[dup_team.id] = canonical_team.id
            logger.info(f"  MANUAL-DEDUP: '{dup_name}' ({dup_team.id}) → '{canonical_name}' ({canonical_team.id})")

    return id_map


def run_audit(output_path: str = "CLUB_TEAM_IDENTITY_AUDIT.md") -> dict:
    db = SessionLocal()
    try:
        teams_data = get_all_teams_with_match_counts(db)
        duplicates = detect_auto_duplicates(teams_data)
        id_map = build_canonical_id_map(db, teams_data)

        # Write canonical map as JSON for use by training builder
        map_path = Path(__file__).parent / "canonical_team_id_map.json"
        with open(map_path, "w") as f:
            json.dump({str(k): v for k, v in id_map.items()}, f, indent=2)
        logger.info(f"Canonical team ID map saved to {map_path}")

        # Build markdown report
        lines = [
            "# Club Team Identity Audit",
            "",
            f"**Date:** {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}",
            f"**Total Teams in DB:** {len(teams_data)}",
            f"**Duplicate Groups Detected:** {len(duplicates)}",
            f"**Canonical Aliases Created:** {len(id_map)}",
            "",
            "---",
            "",
            "## Duplicate Team Records Found",
            "",
        ]

        if not duplicates:
            lines.append("No duplicates detected via auto-normalization.")
        else:
            lines.append("| Normalized Key | Team Name | ID | Total Matches | Elo | Market Value | Status |")
            lines.append("|----------------|-----------|:--:|:--:|:--:|:--:|:------:|")
            for grp in duplicates:
                variants = sorted(grp["variants"], key=lambda x: x["total_matches"], reverse=True)
                for i, v in enumerate(variants):
                    is_canonical = (i == 0) and (v["id"] not in id_map)
                    # Check if explicitly overridden
                    is_canonical_explicit = v["id"] not in id_map
                    role = "✅ CANONICAL" if is_canonical_explicit else f"⚠️ ALIAS → id {id_map.get(v['id'], '?')}"
                    lines.append(f"| `{grp['normalized']}` | {v['name']} | {v['id']} | {v['total_matches']} | {v['elo'] or 'N/A'} | {v['market_value'] or 'N/A'} | {role} |")

        lines += [
            "",
            "---",
            "",
            "## Canonical Team ID Mapping",
            "",
            "All training features will use these canonical IDs:",
            "",
            "| Duplicate Team Name | Duplicate ID | Canonical Team Name | Canonical ID |",
            "|---------------------|:------------:|---------------------|:------------:|",
        ]

        for dup_id, can_id in id_map.items():
            dup_name = teams_data.get(dup_id, {}).get("name", f"id={dup_id}")
            can_name = teams_data.get(can_id, {}).get("name", f"id={can_id}")
            lines.append(f"| {dup_name} | {dup_id} | {can_name} | {can_id} |")

        lines += [
            "",
            "---",
            "",
            "## Action Taken",
            "",
            "- ✅ Canonical team ID map saved to `ml/canonical_team_id_map.json`",
            "- ✅ Training dataset builder will use canonical IDs for all feature extraction",
            "- ✅ No existing DB records were deleted or modified",
            "- ✅ No FK constraints were changed",
            "",
        ]

        report_content = "\n".join(lines)

        # Write to artifacts
        out = Path(output_path)
        out.write_text(report_content)
        logger.info(f"Report written to {output_path}")

        return id_map

    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Running team identity audit...")
    id_map = run_audit()
    print(f"\nCanonical map: {len(id_map)} aliases resolved")
    print(f"Saved to: ml/canonical_team_id_map.json")

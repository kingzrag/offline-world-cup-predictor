"""
ml/export_elo_seed.py
=====================
Compute ELO ratings directly from the international results CSV
and write them as PostgreSQL UPSERT statements that can be pasted
into Render's psql console or added as a migration.

Usage:
    python3 -m ml.export_elo_seed --csv data/international/results.csv

Output:
    prints SQL to stdout (redirect to a .sql file)
"""
import csv
import math
import argparse
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INITIAL_ELO = 1500
K_FACTORS = {
    "FIFA World Cup": 60,
    "UEFA Euro": 50,
    "Copa America": 50,
    "African Cup of Nations": 50,
    "AFC Asian Cup": 50,
    "CONCACAF Gold Cup": 40,
    "CONCACAF Nations League": 40,
    "UEFA Nations League": 40,
    "World Cup qualification": 40,
    "FIFA World Cup qualification": 40,
    "UEFA Euro qualification": 40,
    "African Cup of Nations qualification": 40,
    "AFC Asian Cup qualification": 40,
    "Friendly": 20,
    "International friendly": 20,
}
DEFAULT_K = 30


def expected_score(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def goal_diff_multiplier(gd: int) -> float:
    g = abs(gd)
    if g <= 1:
        return 1.0
    elif g == 2:
        return 1.5
    elif g == 3:
        return 1.75
    else:
        return 1.75 + (g - 3) * 0.125


def compute_elo(csv_path: str) -> dict:
    ratings: dict[str, float] = {}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Sort chronologically (some files are already sorted but just in case)
    rows.sort(key=lambda r: r.get("date", ""))

    for row in rows:
        home = row.get("home_team", "").strip()
        away = row.get("away_team", "").strip()
        tournament = row.get("tournament", "Friendly").strip()

        try:
            hs = int(row.get("home_score", 0) or 0)
            as_ = int(row.get("away_score", 0) or 0)
        except ValueError:
            continue

        if not home or not away:
            continue

        ra = ratings.setdefault(home, INITIAL_ELO)
        rb = ratings.setdefault(away, INITIAL_ELO)

        K = K_FACTORS.get(tournament, DEFAULT_K)
        gd = hs - as_
        mult = goal_diff_multiplier(gd)

        if hs > as_:
            sa, sb = 1.0, 0.0
        elif hs == as_:
            sa, sb = 0.5, 0.5
        else:
            sa, sb = 0.0, 1.0

        ea = expected_score(ra, rb)
        eb = expected_score(rb, ra)

        ratings[home] = ra + K * mult * (sa - ea)
        ratings[away] = rb + K * mult * (sb - eb)

    return {name: round(r) for name, r in ratings.items()}


# ---------------------------------------------------------------------------
# World Cup 2026 qualified teams (name as used in the CSV)
# ---------------------------------------------------------------------------
WC_TEAMS = {
    "Brazil", "Argentina", "France", "England", "Spain", "Germany",
    "Portugal", "Netherlands", "Belgium", "Italy", "Mexico", "United States",
    "Canada", "Uruguay", "Colombia", "Chile", "Ecuador", "Peru",
    "Morocco", "Senegal", "Nigeria", "Ghana", "Cameroon", "Ivory Coast",
    "Japan", "South Korea", "Australia", "Iran", "Saudi Arabia", "Qatar",
    "Croatia", "Serbia", "Switzerland", "Denmark", "Poland", "Sweden",
    "Austria", "Hungary", "Scotland", "Turkey", "Czech Republic",
    "Algeria", "Egypt", "Tunisia", "Cameroon", "DR Congo",
    "Uzbekistan", "New Zealand", "Panama", "Honduras", "Costa Rica",
    "Jamaica", "Venezuela", "Bolivia", "Paraguay"
}


def main():
    parser = argparse.ArgumentParser(description="Export ELO seed SQL from CSV")
    parser.add_argument(
        "--csv",
        default="data/international/results.csv",
        help="Path to international results CSV"
    )
    parser.add_argument(
        "--all-teams",
        action="store_true",
        help="Export all teams, not just WC teams"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    print(f"-- Computing ELO from {csv_path} ...", flush=True)
    ratings = compute_elo(str(csv_path))
    print(f"-- Computed ELO for {len(ratings)} teams.", flush=True)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if args.all_teams:
        teams_to_export = sorted(ratings.keys())
    else:
        # Export WC teams + any team with elo > 1600 (significant national teams)
        teams_to_export = sorted(
            name for name, elo in ratings.items()
            if name in WC_TEAMS or elo >= 1600
        )

    print(f"-- Exporting {len(teams_to_export)} teams.")
    print()
    print("-- =================================================================")
    print("-- ELO Seed: generated from international results CSV")
    print(f"-- Generated at: {now} UTC")
    print("-- =================================================================")
    print()
    print("BEGIN;")
    print()

    for name in teams_to_export:
        elo = ratings[name]
        safe_name = name.replace("'", "''")
        print(
            f"INSERT INTO team_elo (team_name, elo_rating, last_updated) "
            f"VALUES ('{safe_name}', {elo}, NOW()) "
            f"ON CONFLICT (team_name) DO UPDATE "
            f"SET elo_rating = EXCLUDED.elo_rating, last_updated = NOW();"
        )

    print()
    print("COMMIT;")
    print()
    print(f"-- Done. {len(teams_to_export)} ELO ratings upserted.")


if __name__ == "__main__":
    main()

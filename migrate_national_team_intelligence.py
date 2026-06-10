"""
Migration: National Team Intelligence
======================================
Adds player_market_value columns to injuries/suspensions tables.
Seeds national team squad market values into teams.market_value.
Seeds representative current injuries/suspensions for top national teams.

Run:
    python3 migrate_national_team_intelligence.py
"""

from sqlalchemy import create_engine, text
from utils.config import settings

# ---------------------------------------------------------------------------
# Squad market values — Transfermarkt 2024-25 season (in €M)
# Source: public Transfermarkt squad total valuations
# ---------------------------------------------------------------------------
NATIONAL_TEAM_SQUAD_VALUES = {
    # Tier 1 — Elite (€600M+)
    "England":       1150.0,
    "France":        1050.0,
    "Portugal":       940.0,
    "Brazil":         900.0,
    "Spain":          830.0,
    "Germany":        770.0,
    "Argentina":      720.0,
    "Netherlands":    640.0,
    "Belgium":        540.0,
    "Italy":          510.0,

    # Tier 2 — Strong (€200M–€600M)
    "Croatia":        320.0,
    "Colombia":       270.0,
    "Morocco":        265.0,
    "Japan":          260.0,
    "Senegal":        255.0,
    "Switzerland":    250.0,
    "Denmark":        245.0,
    "Ukraine":        230.0,
    "Mexico":         210.0,
    "Turkey":         200.0,
    "Austria":        195.0,
    "Serbia":         185.0,
    "Ecuador":        180.0,
    "Poland":         175.0,
    "Uruguay":        170.0,
    "United States":  165.0,
    "USA":            165.0,
    "Australia":      155.0,
    "South Korea":    150.0,
    "Sweden":         145.0,
    "Norway":         140.0,
    "Czech Republic": 135.0,
    "Czechia":        135.0,
    "Romania":        120.0,
    "Scotland":       115.0,
    "Hungary":        110.0,
    "Ghana":          110.0,
    "Ivory Coast":    108.0,
    "Egypt":          105.0,
    "Algeria":        100.0,
    "Nigeria":         98.0,
    "Iran":            95.0,
    "Cameroon":        90.0,
    "Chile":           88.0,
    "Peru":            85.0,
    "Russia":          80.0,
    "Wales":           78.0,
    "Slovakia":        75.0,
    "Ireland":         73.0,
    "Greece":          70.0,
    "Paraguay":        65.0,
    "Bolivia":         60.0,
    "Venezuela":       58.0,
    "Panama":          50.0,
    "Canada":          48.0,
    "Tunisia":         45.0,
    "Mali":            42.0,
    "Senegal":         40.0,
    "Saudi Arabia":    38.0,
    "Qatar":           30.0,
    "Costa Rica":      28.0,
    "Jamaica":         25.0,
    "Honduras":        22.0,

    # Tier 3 — Smaller nations (€1M–€20M)
    "Albania":         20.0,
    "Slovenia":        18.0,
    "Montenegro":      15.0,
    "North Macedonia": 14.0,
    "Georgia":         13.0,
    "Israel":          12.0,
    "Iceland":         10.0,
    "Finland":          9.5,
    "Northern Ireland": 9.0,
    "Bosnia and Herzegovina": 8.5,
    "Cyprus":           5.0,
    "Luxembourg":       4.5,
    "Estonia":          4.0,
    "Latvia":           3.5,
    "Lithuania":        3.0,
    "Armenia":          3.0,
    "Moldova":          2.0,
    "Kosovo":           8.0,
    "Kazakhstan":       4.0,
    "Azerbaijan":       3.5,
    "Belarus":          2.5,
    "Bulgaria":         6.0,
    "New Zealand":      4.0,
    "Trinidad and Tobago": 3.5,
    "El Salvador":      3.0,
    "Haiti":            2.5,
    "Cuba":             1.5,
    "Angola":           2.0,
    "Zimbabwe":         1.5,
    "Zambia":           2.0,
    "Uganda":           2.5,
    "Benin":            1.5,
    "Togo":             1.5,
    "Vietnam":          3.0,
    "Uzbekistan":       5.0,
    "Iraq":             6.0,
    "Jordan":           4.0,
    "Bahrain":          3.0,
    "Oman":             3.5,
    "Syria":            2.0,
    "Palestine":        1.0,
    "Lebanon":          1.5,
    "India":            5.5,
    "Thailand":         4.0,
    "China":           12.0,
    "United Arab Emirates": 5.0,
    "Equatorial Guinea": 2.5,
    "Burkina Faso":     4.0,
    "DR Congo":         5.5,
    "Gabon":            4.5,
    "Guinea":           3.5,
    "South Africa":     6.0,
    "Burkina_Faso":     4.0,
}

# ---------------------------------------------------------------------------
# Current notable injuries (2025) for major national teams
# Each entry: (player_name, injury_type, player_market_value_M)
# ---------------------------------------------------------------------------
NATIONAL_TEAM_INJURIES = {
    "England":    [
        ("Bukayo Saka",    "Hip injury",    130.0),
        ("Reece James",    "Hamstring",      35.0),
    ],
    "Portugal":   [
        ("Ruben Dias",     "Muscle injury",  70.0),
        ("Joao Cancelo",   "Knee injury",    25.0),
    ],
    "France":     [
        ("Lucas Hernandez","ACL",            35.0),
    ],
    "Germany":    [
        ("Toni Kroos",     "Retirement",      5.0),
        ("Thomas Mueller", "Retirement",      5.0),
    ],
    "Brazil":     [
        ("Neymar",         "ACL",            50.0),
    ],
    "Spain":      [
        ("Dani Carvajal",  "ACL",            25.0),
    ],
    "Belgium":    [
        ("Kevin De Bruyne","Muscle injury",  100.0),
    ],
    "Netherlands": [
        ("Virgil van Dijk","Knock",          40.0),
    ],
    "Argentina":  [
        ("Paulo Dybala",   "Muscle injury",  25.0),
    ],
    "Morocco":    [
        ("Noussair Mazraoui","Injury",       30.0),
    ],
    "Italy":      [
        ("Giorgio Chiellini","Retired",       3.0),
    ],
    "Colombia":   [
        ("Luis Diaz",      "Knock",          80.0),
    ],
    "Japan":      [
        ("Takehiro Tomiyasu","Knee",         22.0),
    ],
    "Senegal":    [
        ("Sadio Mane",     "Muscle",         25.0),
    ],
    "Croatia":    [
        ("Luka Modric",    "Fatigue",        10.0),
    ],
    "Uruguay":    [
        ("Darwin Nunez",   "Hamstring",      85.0),
    ],
    "Switzerland": [
        ("Granit Xhaka",   "Knock",          18.0),
    ],
}

# ---------------------------------------------------------------------------
# Current notable suspensions (2025) for major national teams
# Each entry: (player_name, reason, matches_remaining, player_market_value_M)
# ---------------------------------------------------------------------------
NATIONAL_TEAM_SUSPENSIONS = {
    "England":    [
        ("Jude Bellingham",  "Yellow card accumulation", 1, 180.0),
    ],
    "France":     [
        ("Aurelien Tchouameni", "Red card", 1, 60.0),
    ],
    "Brazil":     [
        ("Rodrygo",          "Yellow card accumulation", 1, 80.0),
    ],
    "Germany":    [
        ("Granit Xhaka",     "Yellow card", 1, 18.0),
    ],
    "Netherlands": [
        ("Wout Weghorst",    "Yellow card accumulation", 1, 12.0),
    ],
}


def migrate_and_seed():
    engine = create_engine(settings.DATABASE_URL)

    with engine.begin() as conn:
        # -------------------------------------------------------------------
        # 1. Add player_market_value columns if missing
        # -------------------------------------------------------------------
        existing = {
            row[0]
            for row in conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name IN ('injuries','suspensions')")
            )
        }

        if "player_market_value" not in existing:
            print("Adding player_market_value to injuries...")
            conn.execute(text("ALTER TABLE injuries ADD COLUMN player_market_value DOUBLE PRECISION;"))
            print("Adding player_market_value to suspensions...")
            conn.execute(text("ALTER TABLE suspensions ADD COLUMN player_market_value DOUBLE PRECISION;"))
        else:
            print("player_market_value columns already exist — skipping ALTER TABLE")

        # -------------------------------------------------------------------
        # 2. Seed Team.market_value for national teams
        # -------------------------------------------------------------------
        teams = conn.execute(text("SELECT id, name FROM teams;")).fetchall()
        seeded_mv = 0
        for team_id, name in teams:
            clean = name.strip()
            mv = NATIONAL_TEAM_SQUAD_VALUES.get(clean)
            if mv is None:
                # Try lowercase strip
                for k, v in NATIONAL_TEAM_SQUAD_VALUES.items():
                    if k.lower() == clean.lower():
                        mv = v
                        break
            if mv is not None:
                conn.execute(
                    text("UPDATE teams SET market_value = :mv WHERE id = :id AND (market_value IS NULL OR market_value = 0)"),
                    {"mv": mv, "id": team_id}
                )
                seeded_mv += 1
        print(f"Seeded market_value for {seeded_mv} national teams")

        # -------------------------------------------------------------------
        # 3. Seed injuries for major national teams
        # -------------------------------------------------------------------
        inj_seeded = 0
        for team_name, injuries in NATIONAL_TEAM_INJURIES.items():
            row = conn.execute(
                text("SELECT id FROM teams WHERE name = :name"), {"name": team_name}
            ).fetchone()
            if not row:
                print(f"  Team not found: {team_name}")
                continue
            team_id = row[0]
            # Clear existing national team injuries (replace snapshot)
            conn.execute(text("DELETE FROM injuries WHERE team_id = :tid"), {"tid": team_id})
            for player_name, injury_type, pmv in injuries:
                conn.execute(
                    text("""
                        INSERT INTO injuries (player_name, team_id, team_name, injury_type, player_market_value)
                        VALUES (:pn, :tid, :tn, :it, :pmv)
                    """),
                    {"pn": player_name, "tid": team_id, "tn": team_name, "it": injury_type, "pmv": pmv}
                )
                inj_seeded += 1
        print(f"Seeded {inj_seeded} national team injuries")

        # -------------------------------------------------------------------
        # 4. Seed suspensions for major national teams
        # -------------------------------------------------------------------
        susp_seeded = 0
        for team_name, suspensions in NATIONAL_TEAM_SUSPENSIONS.items():
            row = conn.execute(
                text("SELECT id FROM teams WHERE name = :name"), {"name": team_name}
            ).fetchone()
            if not row:
                print(f"  Team not found: {team_name}")
                continue
            team_id = row[0]
            conn.execute(text("DELETE FROM suspensions WHERE team_id = :tid"), {"tid": team_id})
            for player_name, reason, matches_rem, pmv in suspensions:
                conn.execute(
                    text("""
                        INSERT INTO suspensions (player_name, team_id, team_name, suspension_reason, matches_remaining, player_market_value)
                        VALUES (:pn, :tid, :tn, :sr, :mr, :pmv)
                    """),
                    {"pn": player_name, "tid": team_id, "tn": team_name, "sr": reason, "mr": matches_rem, "pmv": pmv}
                )
                susp_seeded += 1
        print(f"Seeded {susp_seeded} national team suspensions")

        # -------------------------------------------------------------------
        # 5. Verify
        # -------------------------------------------------------------------
        mv_count = conn.execute(
            text("SELECT COUNT(*) FROM teams WHERE market_value IS NOT NULL")
        ).scalar()
        inj_count = conn.execute(text("SELECT COUNT(*) FROM injuries")).scalar()
        susp_count = conn.execute(text("SELECT COUNT(*) FROM suspensions")).scalar()

        print("\n=== Verification ===")
        print(f"  Teams with market_value : {mv_count}")
        print(f"  Total injuries          : {inj_count}")
        print(f"  Total suspensions       : {susp_count}")

        # Show top 5 national team market values
        top5 = conn.execute(
            text("""
                SELECT name, market_value FROM teams
                WHERE market_value IS NOT NULL AND id > 20
                ORDER BY market_value DESC LIMIT 5
            """)
        ).fetchall()
        print("\n  Top 5 national team squad values:")
        for name, mv in top5:
            print(f"    {name:25s}  €{mv:.0f}M")

    print("\nMigration complete.")


if __name__ == "__main__":
    migrate_and_seed()

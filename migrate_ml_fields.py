from sqlalchemy import create_engine, text
from utils.config import settings

# Static database seeding data for FIFA rankings (national teams) and Market Values (clubs & nations)
# Market values are represented in Millions of Euros
SEED_DATA = {
    # Premier League Clubs
    "Arsenal FC": {"fifa_ranking": None, "market_value": 1120.0},
    "Manchester City FC": {"fifa_ranking": None, "market_value": 1260.0},
    "Manchester United FC": {"fifa_ranking": None, "market_value": 730.0},
    "Aston Villa FC": {"fifa_ranking": None, "market_value": 640.0},
    "Liverpool FC": {"fifa_ranking": None, "market_value": 920.0},
    "AFC Bournemouth": {"fifa_ranking": None, "market_value": 350.0},
    "Sunderland AFC": {"fifa_ranking": None, "market_value": 80.0},
    "Brighton & Hove Albion FC": {"fifa_ranking": None, "market_value": 490.0},
    "Brentford FC": {"fifa_ranking": None, "market_value": 410.0},
    "Chelsea FC": {"fifa_ranking": None, "market_value": 950.0},
    "Fulham FC": {"fifa_ranking": None, "market_value": 340.0},
    "Newcastle United FC": {"fifa_ranking": None, "market_value": 650.0},
    "Everton FC": {"fifa_ranking": None, "market_value": 340.0},
    "Leeds United FC": {"fifa_ranking": None, "market_value": 220.0},
    "Crystal Palace FC": {"fifa_ranking": None, "market_value": 430.0},
    "Nottingham Forest FC": {"fifa_ranking": None, "market_value": 370.0},
    "Tottenham Hotspur FC": {"fifa_ranking": None, "market_value": 770.0},
    "West Ham United FC": {"fifa_ranking": None, "market_value": 460.0},
    "Burnley FC": {"fifa_ranking": None, "market_value": 250.0},
    "Wolverhampton Wanderers FC": {"fifa_ranking": None, "market_value": 380.0},

    # World Cup National Teams (Example Seed Data for international matches)
    "Argentina": {"fifa_ranking": 1, "market_value": 720.0},
    "France": {"fifa_ranking": 2, "market_value": 1020.0},
    "England": {"fifa_ranking": 3, "market_value": 1150.0},
    "Belgium": {"fifa_ranking": 4, "market_value": 540.0},
    "Brazil": {"fifa_ranking": 5, "market_value": 980.0},
    "Portugal": {"fifa_ranking": 6, "market_value": 930.0},
    "Netherlands": {"fifa_ranking": 7, "market_value": 610.0},
    "Spain": {"fifa_ranking": 8, "market_value": 830.0},
    "Italy": {"fifa_ranking": 9, "market_value": 640.0},
    "Croatia": {"fifa_ranking": 10, "market_value": 320.0},
    "USA": {"fifa_ranking": 11, "market_value": 310.0},
    "Germany": {"fifa_ranking": 12, "market_value": 750.0},
    "Morocco": {"fifa_ranking": 13, "market_value": 350.0},
    "Uruguay": {"fifa_ranking": 14, "market_value": 420.0},
    "Switzerland": {"fifa_ranking": 15, "market_value": 280.0},
    "Colombia": {"fifa_ranking": 16, "market_value": 250.0},
    "Mexico": {"fifa_ranking": 17, "market_value": 210.0},
    "Japan": {"fifa_ranking": 18, "market_value": 290.0},
    "Senegal": {"fifa_ranking": 19, "market_value": 300.0},
    "Iran": {"fifa_ranking": 20, "market_value": 50.0},
    "Canada": {"fifa_ranking": 40, "market_value": 180.0},
}

def migrate_and_seed():
    db_url = settings.DATABASE_URL
    print(f"Connecting to database...")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        # 1. Add columns to table `teams` if they do not exist
        print("Checking if columns exist in teams table...")
        columns_res = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='teams';"
        ))
        existing_cols = {row[0] for row in columns_res}
        
        if "fifa_ranking" not in existing_cols:
            print("Adding fifa_ranking column to teams table...")
            conn.execute(text("ALTER TABLE teams ADD COLUMN fifa_ranking INTEGER;"))
        if "market_value" not in existing_cols:
            print("Adding market_value column to teams table...")
            conn.execute(text("ALTER TABLE teams ADD COLUMN market_value DOUBLE PRECISION;"))
            
        print("Columns checked/added successfully.")
        
        # 2. Seed the team fields based on matching names
        print("Seeding team parameters...")
        teams_res = conn.execute(text("SELECT id, name FROM teams;"))
        db_teams = teams_res.fetchall()
        
        seeded_count = 0
        for team_id, name in db_teams:
            # Flexible matching for team name
            seed_info = None
            for key, val in SEED_DATA.items():
                if name.lower().strip() == key.lower().strip() or name.lower().replace("fc", "").strip() == key.lower().replace("fc", "").strip():
                    seed_info = val
                    break
            
            if seed_info:
                conn.execute(text(
                    "UPDATE teams SET fifa_ranking = :fifa, market_value = :mv WHERE id = :id;"
                ), {"fifa": seed_info["fifa_ranking"], "mv": seed_info["market_value"], "id": team_id})
                seeded_count += 1
                
        print(f"Migration completed. Successfully seeded {seeded_count} teams in database.")

if __name__ == "__main__":
    migrate_and_seed()

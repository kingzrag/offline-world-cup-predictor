"""
Migration script for National Team Intelligence Pipeline tables.
"""
from sqlalchemy import create_engine, text
from utils.config import settings

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        print("1. Checking and adding squad_market_value column in teams table...")
        columns_res = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='teams';"
        ))
        existing_cols = {row[0] for row in columns_res}
        if "squad_market_value" not in existing_cols:
            print("Adding squad_market_value to teams table...")
            conn.execute(text("ALTER TABLE teams ADD COLUMN squad_market_value DOUBLE PRECISION;"))
        else:
            print("squad_market_value column already exists in teams.")

        print("2. Creating national_team_players table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS national_team_players (
                id SERIAL PRIMARY KEY,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                player_name VARCHAR(100) NOT NULL,
                position VARCHAR(50),
                age INTEGER,
                market_value DOUBLE PRECISION,
                transfermarkt_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS ix_national_team_players_id ON national_team_players(id);
            CREATE INDEX IF NOT EXISTS ix_national_team_players_team_id ON national_team_players(team_id);
        """))

        print("3. Creating national_team_injuries table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS national_team_injuries (
                id SERIAL PRIMARY KEY,
                player_name VARCHAR(100) NOT NULL,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                team_name VARCHAR(100) NOT NULL,
                injury_status VARCHAR(100),
                injury_description VARCHAR(255),
                expected_return_date DATE,
                market_value_impact DOUBLE PRECISION,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS ix_national_team_injuries_id ON national_team_injuries(id);
            CREATE INDEX IF NOT EXISTS ix_national_team_injuries_team_id ON national_team_injuries(team_id);
        """))

        print("4. Creating national_team_suspensions table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS national_team_suspensions (
                id SERIAL PRIMARY KEY,
                player_name VARCHAR(100) NOT NULL,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                team_name VARCHAR(100) NOT NULL,
                suspension_reason VARCHAR(255),
                matches_remaining INTEGER,
                market_value_impact DOUBLE PRECISION,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS ix_national_team_suspensions_id ON national_team_suspensions(id);
            CREATE INDEX IF NOT EXISTS ix_national_team_suspensions_team_id ON national_team_suspensions(team_id);
        """))

        print("Migration run successfully.")

if __name__ == "__main__":
    run_migration()

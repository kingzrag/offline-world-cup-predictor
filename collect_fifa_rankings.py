import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.fifa_ranking_service import fetch_fifa_rankings, upsert_fifa_rankings
from utils.logger import logger

# ----------------------------------------------------------------------
# Database connection helper (mirrors other collector scripts)
# ----------------------------------------------------------------------
def get_engine():
    from dotenv import load_dotenv
    load_dotenv()
    user = os.getenv("DATABASE_USER") or os.getlogin()
    password = os.getenv("DATABASE_PASSWORD") or ""
    host = os.getenv("DATABASE_HOST") or "localhost"
    port = os.getenv("DATABASE_PORT") or "5432"
    db_name = os.getenv("DATABASE_NAME") or "prediction_db"
    url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(url, echo=False)


def main():
    logger.info("Starting FIFA ranking collection")
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    with Session() as db:
        rankings = fetch_fifa_rankings()
        upsert_fifa_rankings(db, rankings)
    logger.info("FIFA ranking collection completed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("FIFA ranking collection failed: %s", e)
        sys.exit(1)

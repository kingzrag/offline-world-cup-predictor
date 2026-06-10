import asyncio
import sys
import argparse

from database.connection import SessionLocal
from services.elo_service import EloService
from utils.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Collect Football ELO Ratings")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = EloService()
        service.ingest_elo_ratings(db)
        logger.info("ELO rating collection completed successfully.")
    except Exception as e:
        logger.error(f"ELO rating collection failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

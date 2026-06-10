import asyncio
import sys
from database.connection import SessionLocal
from services.odds_service import OddsService
from utils.logger import logger

async def main():
    db = SessionLocal()
    service = OddsService()
    try:
        raw_odds = service.fetch_upcoming_odds()
        if not raw_odds:
            logger.warning("No odds data retrieved from The Odds API.")
            return
        service.store_odds(db, raw_odds)
        logger.info("Odds collection completed successfully.")
    except Exception as exc:
        logger.error(f"Odds collection failed: {exc}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

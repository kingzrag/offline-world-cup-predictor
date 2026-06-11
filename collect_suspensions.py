import asyncio
import sys
import argparse

from database.connection import SessionLocal
from services.collection_service import CollectionService
from utils.logger import logger

async def main():
    parser = argparse.ArgumentParser(description="Collect Suspensions Data")
    parser.add_argument("--competition", type=str, default="WC", help="Competition code (e.g. PL, PD, SA)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = CollectionService()
        await service.ingest_suspensions(db, args.competition)
        logger.info("Suspension collection completed successfully.")
    except Exception as e:
        logger.error(f"Suspension collection failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

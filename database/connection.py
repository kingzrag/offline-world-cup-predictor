from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from utils.config import settings

from utils.logger import logger
import sys

# Create engine with production-grade configurations
# pool_pre_ping checks the connection health before executing commands
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True
    )
except Exception as e:
    logger.error(f"Failed to initialize database engine. Please check your connection URL and ensure Postgres is running. Details: {e}")
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator for FastAPI routes to retrieve a db session.
    Ensures that session is closed after execution.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

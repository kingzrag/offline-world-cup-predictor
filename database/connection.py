from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from utils.config import settings

from utils.logger import logger
import sys

# Create engine with production-grade configurations
# pool_pre_ping checks the connection health before executing commands
try:
    import os
    pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_timeout=10,
        pool_pre_ping=True,
        echo=False
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
    except Exception as e:
        db.rollback()
        logger.error(f"Database error, transaction rolled back: {e}", exc_info=True)
        raise
    finally:
        db.close()

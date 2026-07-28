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
    pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
    statement_timeout = int(os.getenv("DB_STATEMENT_TIMEOUT", "30"))
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,
        connect_args={"connect_timeout": connect_timeout},
        echo=False  # Set to True for SQL query logging in development
    )
    
    # Set statement timeout for all connections
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET statement_timeout TO {statement_timeout * 1000}")  # Convert to milliseconds
        cursor.close()
        
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

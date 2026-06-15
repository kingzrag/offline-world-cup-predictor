"""
Run Alembic migrations and verify ORM schema matches the database.
"""
from sqlalchemy import inspect

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from database.connection import engine
from models.match import Match
from utils.config import settings
from utils.logger import logger


def run_migrations() -> str:
    """
    Apply all pending Alembic revisions.
    Returns the current head revision id after upgrade.
    """
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    logger.info("Running Alembic migrations (upgrade head)...")
    command.upgrade(alembic_cfg, "head")

    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()
    logger.info(f"Alembic migrations complete — head revision: {head}")
    return head or ""


def verify_matches_schema() -> None:
    """
    Confirm columns defined on Match exist in PostgreSQL.
    Raises RuntimeError when a required column is missing.
    """
    inspector = inspect(engine)
    if "matches" not in inspector.get_table_names():
        raise RuntimeError("Schema verification failed: matches table does not exist")

    db_columns = {col["name"] for col in inspector.get_columns("matches")}
    model_columns = {col.name for col in Match.__table__.columns}
    missing = sorted(model_columns - db_columns)

    if missing:
        raise RuntimeError(
            f"Schema verification failed: matches table missing columns {missing}"
        )

    logger.info(
        f"Schema verification passed — matches table has all {len(model_columns)} model columns"
    )

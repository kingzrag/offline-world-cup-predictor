"""
ml/seed_elo.py
==============
Upserts pre-computed ELO ratings into team_elo table on startup.
Safe to call multiple times — uses ON CONFLICT DO UPDATE.

Called from main.py lifespan startup event.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.team_elo import TeamElo
from ml.elo_seed_data import ELO_RATINGS

logger = logging.getLogger(__name__)


def seed_elo_ratings(db: Session) -> None:
    """
    Upserts ELO ratings from the pre-computed seed data.
    Only runs if the team_elo table has fewer than 10 rows, to avoid
    overwriting freshly-computed ratings from the full pipeline.
    """
    existing_count = db.query(TeamElo).count()
    if existing_count >= len(ELO_RATINGS):
        logger.info(
            f"[seed_elo] team_elo table already has {existing_count} rows "
            f"(>= {len(ELO_RATINGS)} seed entries) — skipping seed."
        )
        return

    logger.info(
        f"[seed_elo] team_elo has {existing_count} rows — "
        f"seeding {len(ELO_RATINGS)} ELO ratings …"
    )

    try:
        stmt = pg_insert(TeamElo).values([
            {"team_name": name, "elo_rating": elo}
            for name, elo in ELO_RATINGS.items()
        ])
        stmt = stmt.on_conflict_do_update(
            index_elements=["team_name"],
            set_={"elo_rating": stmt.excluded.elo_rating}
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"[seed_elo] Seeded {len(ELO_RATINGS)} ELO ratings successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"[seed_elo] Failed to seed ELO ratings: {e}", exc_info=True)

"""
ml/seed_elo.py
==============
Seeds the Render database on startup with pre-computed data so that
the prediction engine produces meaningful results immediately.

Seeds:
  1. team_elo table   — ELO ratings from 49K+ international matches
  2. teams table      — FIFA rankings + squad market values

Safe to call multiple times — uses ON CONFLICT DO UPDATE / conditional updates.
Called from main.py lifespan startup event.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.team_elo import TeamElo
from models.team import Team
from ml.elo_seed_data import ELO_RATINGS
from ml.team_seed_data import TEAM_DATA

logger = logging.getLogger(__name__)


def seed_elo_ratings(db: Session) -> None:
    """
    Upserts ELO ratings from the pre-computed seed data.
    Skips if the table already has enough rows.
    """
    existing_count = db.query(TeamElo).count()
    if existing_count >= len(ELO_RATINGS):
        logger.info(
            f"[seed_elo] team_elo already has {existing_count} rows "
            f"(>= {len(ELO_RATINGS)} seed entries) — skipping ELO seed."
        )
    else:
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
            logger.info(f"[seed_elo] Seeded {len(ELO_RATINGS)} ELO ratings ✓")
        except Exception as e:
            db.rollback()
            logger.error(f"[seed_elo] Failed to seed ELO ratings: {e}", exc_info=True)

    # ── Seed FIFA rankings + squad market values ─────────────────────────────
    _seed_team_metadata(db)


def _seed_team_metadata(db: Session) -> None:
    """
    Updates teams.fifa_ranking and teams.squad_market_value for every
    team in TEAM_DATA that already exists in the teams table.
    Only updates rows where the column is currently NULL.
    """
    updated = 0
    skipped = 0

    for team_name, (fifa_rank, squad_mv) in TEAM_DATA.items():
        team = db.query(Team).filter(Team.name.ilike(team_name), Team.gender == "MEN").first()
        if not team:
            skipped += 1
            continue

        changed = False
        if team.fifa_ranking is None or team.fifa_ranking == 150:
            team.fifa_ranking = fifa_rank
            changed = True
        if team.squad_market_value is None or team.squad_market_value == 0:
            team.squad_market_value = squad_mv
            changed = True

        if changed:
            updated += 1

    if updated > 0:
        try:
            db.commit()
            logger.info(
                f"[seed_elo] Updated {updated} teams with FIFA rank + squad value "
                f"({skipped} teams not found in DB)"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"[seed_elo] Failed to seed team metadata: {e}", exc_info=True)
    else:
        logger.info(
            f"[seed_elo] All {len(TEAM_DATA)} teams already have FIFA rank + squad value — "
            f"skipping team metadata seed."
        )

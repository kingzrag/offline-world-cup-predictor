"""Add extended stats columns for FBref, StatsBomb, and API-Football data

Revision ID: a1b2c3d4e5f6
Revises: 89fe0513228c
Create Date: 2026-06-26 15:30:00.000000

Adds the following columns (all nullable for backward compatibility):

match_statistics:
  - home_passes, away_passes (Integer)
  - home_pass_accuracy, away_pass_accuracy (Float, 0-100)
  - home_tackles, away_tackles (Integer)
  - home_interceptions, away_interceptions (Integer)
  - home_aerial_duels, away_aerial_duels (Integer)
  - data_source (String, which provider stored this row)

player_match_performances:
  - aerial_duels (Integer)
  - aerial_duels_won (Integer)
  - fbref_id (String)
  - statsbomb_id (String)
  - statsbomb_xg (Float)
  - key_passes (Integer)
  - dribbles_completed (Integer)
  - clearances (Integer)
  - blocks (Integer)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import logging

logger = logging.getLogger('alembic')

# revision identifiers
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '89fe0513228c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    conn = op.get_bind()

    # -----------------------------------------------------------------
    # match_statistics — add extended stats columns
    # -----------------------------------------------------------------
    match_stat_columns = [
        ("home_passes", sa.Integer(), True),
        ("away_passes", sa.Integer(), True),
        ("home_pass_accuracy", sa.Float(), True),
        ("away_pass_accuracy", sa.Float(), True),
        ("home_tackles", sa.Integer(), True),
        ("away_tackles", sa.Integer(), True),
        ("home_interceptions", sa.Integer(), True),
        ("away_interceptions", sa.Integer(), True),
        ("home_aerial_duels", sa.Integer(), True),
        ("away_aerial_duels", sa.Integer(), True),
        ("data_source", sa.String(50), True),
    ]

    for col_name, col_type, nullable in match_stat_columns:
        if not _column_exists(conn, "match_statistics", col_name):
            logger.info(f"Adding column match_statistics.{col_name}")
            op.add_column(
                "match_statistics",
                sa.Column(col_name, col_type, nullable=nullable),
            )
        else:
            logger.info(f"Column match_statistics.{col_name} already exists, skipping")

    # -----------------------------------------------------------------
    # player_match_performances — add extended player stats columns
    # -----------------------------------------------------------------
    player_perf_columns = [
        ("aerial_duels", sa.Integer(), True),
        ("aerial_duels_won", sa.Integer(), True),
        ("fbref_id", sa.String(100), True),
        ("statsbomb_id", sa.String(100), True),
        ("statsbomb_xg", sa.Float(), True),
        ("key_passes", sa.Integer(), True),
        ("dribbles_completed", sa.Integer(), True),
        ("clearances", sa.Integer(), True),
        ("blocks", sa.Integer(), True),
    ]

    for col_name, col_type, nullable in player_perf_columns:
        if not _column_exists(conn, "player_match_performances", col_name):
            logger.info(f"Adding column player_match_performances.{col_name}")
            op.add_column(
                "player_match_performances",
                sa.Column(col_name, col_type, nullable=nullable),
            )
        else:
            logger.info(f"Column player_match_performances.{col_name} already exists, skipping")

    logger.info("Extended stats migration complete")


def downgrade() -> None:
    conn = op.get_bind()

    # Remove match_statistics columns
    for col_name in [
        "home_passes", "away_passes",
        "home_pass_accuracy", "away_pass_accuracy",
        "home_tackles", "away_tackles",
        "home_interceptions", "away_interceptions",
        "home_aerial_duels", "away_aerial_duels",
        "data_source",
    ]:
        if _column_exists(conn, "match_statistics", col_name):
            op.drop_column("match_statistics", col_name)

    # Remove player_match_performances columns
    for col_name in [
        "aerial_duels", "aerial_duels_won",
        "fbref_id", "statsbomb_id", "statsbomb_xg",
        "key_passes", "dribbles_completed", "clearances", "blocks",
    ]:
        if _column_exists(conn, "player_match_performances", col_name):
            op.drop_column("player_match_performances", col_name)

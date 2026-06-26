"""Add provider storage columns for StatsBomb and richer player/match stats

Revision ID: 20260626_0004
Revises: a1b2c3d4e5f6
Create Date: 2026-06-26 17:55:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260626_0004"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def _index_exists(conn, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    conn = op.get_bind()

    if not _column_exists(conn, "matches", "statsbomb_id"):
        op.add_column(
            "matches", sa.Column("statsbomb_id", sa.String(length=50), nullable=True)
        )
    if not _index_exists(conn, "matches", "ix_matches_statsbomb_id"):
        op.create_index(
            "ix_matches_statsbomb_id", "matches", ["statsbomb_id"], unique=True
        )

    for col_name, col_type in [
        ("home_successful_passes", sa.Integer()),
        ("away_successful_passes", sa.Integer()),
        ("home_pressures", sa.Integer()),
        ("away_pressures", sa.Integer()),
        ("home_carries", sa.Integer()),
        ("away_carries", sa.Integer()),
    ]:
        if not _column_exists(conn, "match_statistics", col_name):
            op.add_column(
                "match_statistics", sa.Column(col_name, col_type, nullable=True)
            )

    for col_name, col_type in [
        ("successful_passes", sa.Integer()),
        ("pressures", sa.Integer()),
        ("carries", sa.Integer()),
    ]:
        if not _column_exists(conn, "player_match_performances", col_name):
            op.add_column(
                "player_match_performances",
                sa.Column(col_name, col_type, nullable=True),
            )


def downgrade() -> None:
    conn = op.get_bind()

    for col_name in ["successful_passes", "pressures", "carries"]:
        if _column_exists(conn, "player_match_performances", col_name):
            op.drop_column("player_match_performances", col_name)

    for col_name in [
        "home_successful_passes",
        "away_successful_passes",
        "home_pressures",
        "away_pressures",
        "home_carries",
        "away_carries",
    ]:
        if _column_exists(conn, "match_statistics", col_name):
            op.drop_column("match_statistics", col_name)

    if _index_exists(conn, "matches", "ix_matches_statsbomb_id"):
        op.drop_index("ix_matches_statsbomb_id", table_name="matches")
    if _column_exists(conn, "matches", "statsbomb_id"):
        op.drop_column("matches", "statsbomb_id")

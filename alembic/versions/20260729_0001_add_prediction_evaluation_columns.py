"""Add prediction evaluation columns to predictions table

Revision ID: 20260729_0001
Revises: 20260627_0007
Create Date: 2026-07-29

This migration adds the missing evaluation columns that were added to the
SQLAlchemy model but never added to the database via migration:
- actual_result: Stores the actual match outcome (HOME_WIN, AWAY_WIN, DRAW)
- is_correct: Boolean flag indicating if prediction was correct
- finished_at: Timestamp when match ended
- evaluated_at: Timestamp when accuracy evaluation was computed
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260729_0001"
down_revision: Union[str, None] = "f8ba6541747c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def _index_exists(conn, table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    """Add prediction evaluation columns to predictions table."""
    conn = op.get_bind()

    # Add actual_result column
    if not _column_exists(conn, "predictions", "actual_result"):
        op.add_column(
            "predictions",
            sa.Column("actual_result", sa.String(length=50), nullable=True)
        )

    # Add is_correct column
    if not _column_exists(conn, "predictions", "is_correct"):
        op.add_column(
            "predictions",
            sa.Column("is_correct", sa.Boolean(), nullable=True)
        )
        # Add index for is_correct column
        if not _index_exists(conn, "predictions", "ix_predictions_is_correct"):
            op.create_index(
                "ix_predictions_is_correct", "predictions", ["is_correct"]
            )

    # Add finished_at column
    if not _column_exists(conn, "predictions", "finished_at"):
        op.add_column(
            "predictions",
            sa.Column("finished_at", sa.DateTime(), nullable=True)
        )

    # Add evaluated_at column
    if not _column_exists(conn, "predictions", "evaluated_at"):
        op.add_column(
            "predictions",
            sa.Column("evaluated_at", sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    """Remove prediction evaluation columns from predictions table."""
    conn = op.get_bind()

    # Drop index first if it exists
    if _index_exists(conn, "predictions", "ix_predictions_is_correct"):
        op.drop_index("ix_predictions_is_correct", table_name="predictions")

    # Drop columns if they exist
    if _column_exists(conn, "predictions", "evaluated_at"):
        op.drop_column("predictions", "evaluated_at")

    if _column_exists(conn, "predictions", "finished_at"):
        op.drop_column("predictions", "finished_at")

    if _column_exists(conn, "predictions", "is_correct"):
        op.drop_column("predictions", "is_correct")

    if _column_exists(conn, "predictions", "actual_result"):
        op.drop_column("predictions", "actual_result")

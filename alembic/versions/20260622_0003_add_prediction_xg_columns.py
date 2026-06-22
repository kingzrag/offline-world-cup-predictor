"""Add expected-goals columns to predictions for offline enrichment storage.

Revision ID: 20260622_0003
Revises: 20260619_0002
Create Date: 2026-06-22
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260622_0003"
down_revision: Union[str, None] = "20260619_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE predictions
        ADD COLUMN IF NOT EXISTS expected_home_goals DOUBLE PRECISION,
        ADD COLUMN IF NOT EXISTS expected_away_goals DOUBLE PRECISION;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE predictions
        DROP COLUMN IF EXISTS expected_home_goals,
        DROP COLUMN IF EXISTS expected_away_goals;
        """
    )

"""Add missing database indexes to matches and predictions.

Revision ID: 20260619_0002
Revises: 20260616_0001
Create Date: 2026-06-19
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260619_0002"
down_revision: Union[str, None] = "20260616_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add matches.competition_id index
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_matches_competition_id 
        ON matches (competition_id);
        """
    )
    # Add matches.status index
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_matches_status 
        ON matches (status);
        """
    )
    # Add predictions.match_id index
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_predictions_match_id 
        ON predictions (match_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_matches_competition_id;")
    op.execute("DROP INDEX IF EXISTS ix_matches_status;")
    op.execute("DROP INDEX IF EXISTS ix_predictions_match_id;")

"""Add live_minute column to matches table.

Revision ID: 20260616_0001
Revises:
Create Date: 2026-06-16

Safe for production: uses IF NOT EXISTS so re-running does not fail when the
column was already added locally via create_all().
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260616_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'matches'
                  AND column_name = 'live_minute'
            ) THEN
                ALTER TABLE matches ADD COLUMN live_minute INTEGER;
                RAISE NOTICE 'Added live_minute column to matches';
            ELSE
                RAISE NOTICE 'Column matches.live_minute already exists — skipping';
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE matches DROP COLUMN IF EXISTS live_minute;")

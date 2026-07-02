"""add_gender_to_teams

Revision ID: f8ba6541747c
Revises: 20260627_0007
Create Date: 2026-07-02 13:04:15.711942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8ba6541747c'
down_revision: Union[str, None] = '20260627_0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add gender column as nullable with server default (VARCHAR(20) as requested)
    op.add_column('teams', sa.Column('gender', sa.String(20), nullable=True, server_default='MEN'))
    
    # Step 2: Update any existing NULL values to 'MEN'
    op.execute("UPDATE teams SET gender = 'MEN' WHERE gender IS NULL")
    
    # Step 3: Alter column to be non-nullable
    op.alter_column('teams', 'gender', nullable=False)


def downgrade() -> None:
    # Remove the gender column
    op.drop_column('teams', 'gender')

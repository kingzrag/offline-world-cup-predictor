"""add live match fields to matches

Revision ID: 1ba737317132
Revises: 20260622_0003
Create Date: 2026-06-25 04:26:42.824328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ba737317132'
down_revision: Union[str, None] = '20260622_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('api_football_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_matches_api_football_id'), 'matches', ['api_football_id'], unique=True)
    op.add_column('matches', sa.Column('current_minute', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('home_red_cards', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('matches', sa.Column('away_red_cards', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('matches', sa.Column('home_yellow_cards', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('matches', sa.Column('away_yellow_cards', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('matches', sa.Column('current_home_score', sa.Integer(), nullable=True))
    op.add_column('matches', sa.Column('current_away_score', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_index(op.f('ix_matches_api_football_id'), table_name='matches')
    op.drop_column('matches', 'api_football_id')
    op.drop_column('matches', 'current_minute')
    op.drop_column('matches', 'home_red_cards')
    op.drop_column('matches', 'away_red_cards')
    op.drop_column('matches', 'home_yellow_cards')
    op.drop_column('matches', 'away_yellow_cards')
    op.drop_column('matches', 'current_home_score')
    op.drop_column('matches', 'current_away_score')

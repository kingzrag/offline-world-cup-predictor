"""Add performance indexes for frequently queried columns

Revision ID: 20260627_0007
Revises: 20260627_0006
Create Date: 2026-06-27 10:46:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '20260627_0007'
down_revision = '20260627_0006'
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for frequently queried columns to improve query performance."""
    
    # Check if indexes already exist before creating them
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Get existing indexes for all relevant tables
    tables_to_check = ['matches', 'teams', 'predictions', 'injuries', 'suspensions']
    existing_indexes = {}
    for table in tables_to_check:
        try:
            existing_indexes[table] = {idx['name'] for idx in inspector.get_indexes(table)}
        except:
            existing_indexes[table] = set()
    
    # Indexes for matches table
    if 'ix_matches_home_team_id' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_home_team_id', 'matches', ['home_team_id'])
    
    if 'ix_matches_away_team_id' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_away_team_id', 'matches', ['away_team_id'])
    
    # Composite index for common query pattern: competition_id + status + utc_date
    if 'ix_matches_competition_status_date' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_competition_status_date', 'matches', ['competition_id', 'status', 'utc_date'])
    
    # Indexes for teams table
    if 'ix_teams_name' not in existing_indexes.get('teams', set()):
        op.create_index('ix_teams_name', 'teams', ['name'])
    
    if 'ix_teams_short_name' not in existing_indexes.get('teams', set()):
        op.create_index('ix_teams_short_name', 'teams', ['short_name'])
    
    if 'ix_teams_tla' not in existing_indexes.get('teams', set()):
        op.create_index('ix_teams_tla', 'teams', ['tla'])
    
    # Index for predictions table
    if 'ix_predictions_match_id' not in existing_indexes.get('predictions', set()):
        op.create_index('ix_predictions_match_id', 'predictions', ['match_id'])
    
    # Index for injuries table
    if 'ix_injuries_team_id' not in existing_indexes.get('injuries', set()):
        op.create_index('ix_injuries_team_id', 'injuries', ['team_id'])
    
    # Index for suspensions table
    if 'ix_suspensions_team_id' not in existing_indexes.get('suspensions', set()):
        op.create_index('ix_suspensions_team_id', 'suspensions', ['team_id'])


def downgrade():
    """Remove the performance indexes."""
    
    # Remove indexes from matches table
    op.drop_index('ix_matches_home_team_id', table_name='matches')
    op.drop_index('ix_matches_away_team_id', table_name='matches')
    op.drop_index('ix_matches_competition_status_date', table_name='matches')
    
    # Remove indexes from teams table
    op.drop_index('ix_teams_name', table_name='teams')
    op.drop_index('ix_teams_short_name', table_name='teams')
    op.drop_index('ix_teams_tla', table_name='teams')
    
    # Remove indexes from predictions table
    op.drop_index('ix_predictions_match_id', table_name='predictions')
    
    # Remove indexes from injuries table
    op.drop_index('ix_injuries_team_id', table_name='injuries')
    
    # Remove indexes from suspensions table
    op.drop_index('ix_suspensions_team_id', table_name='suspensions')

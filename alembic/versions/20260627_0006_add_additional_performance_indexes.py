"""Add additional performance indexes for remaining frequently queried columns

Revision ID: 20260627_0006
Revises: 20260627_0005
Create Date: 2026-06-27 11:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '20260627_0006'
down_revision = '20260627_0005'
branch_labels = None
depends_on = None


def upgrade():
    """Add additional indexes for frequently queried columns to improve query performance."""
    
    # Check if indexes already exist before creating them
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Get existing indexes for all relevant tables
    tables_to_check = ['matches', 'teams', 'players', 'injuries', 'suspensions', 'predictions', 'bookmaker_odds', 'calibration_metrics', 'prediction_accuracy', 'rolling_accuracy']
    existing_indexes = {}
    for table in tables_to_check:
        try:
            existing_indexes[table] = {idx['name'] for idx in inspector.get_indexes(table)}
        except:
            existing_indexes[table] = set()
    
    # Additional indexes for matches table
    if 'ix_matches_status' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_status', 'matches', ['status'])
    
    if 'ix_matches_stage' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_stage', 'matches', ['stage'])
    
    if 'ix_matches_group' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_group', 'matches', ['group'])
    
    if 'ix_matches_utc_date' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_utc_date', 'matches', ['utc_date'])
    
    if 'ix_matches_winner' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_winner', 'matches', ['winner'])
    
    # Composite index for live matches query
    if 'ix_matches_status_utc_date' not in existing_indexes.get('matches', set()):
        op.create_index('ix_matches_status_utc_date', 'matches', ['status', 'utc_date'])
    
    # Indexes for players table
    if 'ix_players_team_id' not in existing_indexes.get('players', set()):
        op.create_index('ix_players_team_id', 'players', ['team_id'])
    
    if 'ix_players_name' not in existing_indexes.get('players', set()):
        op.create_index('ix_players_name', 'players', ['name'])
    
    if 'ix_players_position' not in existing_indexes.get('players', set()):
        op.create_index('ix_players_position', 'players', ['position'])
    
    if 'ix_players_nationality' not in existing_indexes.get('players', set()):
        op.create_index('ix_players_nationality', 'players', ['nationality'])
    
    # Indexes for injuries table
    if 'ix_injuries_player_name' not in existing_indexes.get('injuries', set()):
        op.create_index('ix_injuries_player_name', 'injuries', ['player_name'])
    
    if 'ix_injuries_expected_return_date' not in existing_indexes.get('injuries', set()):
        op.create_index('ix_injuries_expected_return_date', 'injuries', ['expected_return_date'])
    
    # Indexes for suspensions table
    if 'ix_suspensions_player_name' not in existing_indexes.get('suspensions', set()):
        op.create_index('ix_suspensions_player_name', 'suspensions', ['player_name'])
    
    # Indexes for predictions table
    if 'ix_predictions_predicted_outcome' not in existing_indexes.get('predictions', set()):
        op.create_index('ix_predictions_predicted_outcome', 'predictions', ['predicted_outcome'])
    
    # Indexes for bookmaker_odds table
    if 'ix_bookmaker_odds_match_id' not in existing_indexes.get('bookmaker_odds', set()):
        op.create_index('ix_bookmaker_odds_match_id', 'bookmaker_odds', ['match_id'])
    
    if 'ix_bookmaker_odds_bookmaker' not in existing_indexes.get('bookmaker_odds', set()):
        op.create_index('ix_bookmaker_odds_bookmaker', 'bookmaker_odds', ['bookmaker'])
    
    # Indexes for calibration_metrics table
    if 'ix_calibration_metrics_market_type' not in existing_indexes.get('calibration_metrics', set()):
        op.create_index('ix_calibration_metrics_market_type', 'calibration_metrics', ['market_type'])
    
    if 'ix_calibration_metrics_confidence_bucket' not in existing_indexes.get('calibration_metrics', set()):
        op.create_index('ix_calibration_metrics_confidence_bucket', 'calibration_metrics', ['confidence_bucket_min', 'confidence_bucket_max'])
    
    # Indexes for prediction_accuracy table
    if 'ix_prediction_accuracy_market_type' not in existing_indexes.get('prediction_accuracy', set()):
        op.create_index('ix_prediction_accuracy_market_type', 'prediction_accuracy', ['market_type'])
    
    if 'ix_prediction_accuracy_window_days' not in existing_indexes.get('prediction_accuracy', set()):
        op.create_index('ix_prediction_accuracy_window_days', 'prediction_accuracy', ['window_days'])
    
    # Indexes for rolling_accuracy table
    if 'ix_rolling_accuracy_market_type' not in existing_indexes.get('rolling_accuracy', set()):
        op.create_index('ix_rolling_accuracy_market_type', 'rolling_accuracy', ['market_type'])
    
    if 'ix_rolling_accuracy_window_days' not in existing_indexes.get('rolling_accuracy', set()):
        op.create_index('ix_rolling_accuracy_window_days', 'rolling_accuracy', ['window_days'])
    
    if 'ix_rolling_accuracy_date' not in existing_indexes.get('rolling_accuracy', set()):
        op.create_index('ix_rolling_accuracy_date', 'rolling_accuracy', ['date'])


def downgrade():
    """Remove the additional performance indexes."""
    
    # Remove indexes from matches table
    op.drop_index('ix_matches_status', table_name='matches')
    op.drop_index('ix_matches_stage', table_name='matches')
    op.drop_index('ix_matches_group', table_name='matches')
    op.drop_index('ix_matches_utc_date', table_name='matches')
    op.drop_index('ix_matches_winner', table_name='matches')
    op.drop_index('ix_matches_status_utc_date', table_name='matches')
    
    # Remove indexes from players table
    op.drop_index('ix_players_team_id', table_name='players')
    op.drop_index('ix_players_name', table_name='players')
    op.drop_index('ix_players_position', table_name='players')
    op.drop_index('ix_players_nationality', table_name='players')
    
    # Remove indexes from injuries table
    op.drop_index('ix_injuries_player_name', table_name='injuries')
    op.drop_index('ix_injuries_expected_return_date', table_name='injuries')
    
    # Remove indexes from suspensions table
    op.drop_index('ix_suspensions_player_name', table_name='suspensions')
    
    # Remove indexes from predictions table
    op.drop_index('ix_predictions_predicted_outcome', table_name='predictions')
    
    # Remove indexes from bookmaker_odds table
    op.drop_index('ix_bookmaker_odds_match_id', table_name='bookmaker_odds')
    op.drop_index('ix_bookmaker_odds_bookmaker', table_name='bookmaker_odds')
    
    # Remove indexes from calibration_metrics table
    op.drop_index('ix_calibration_metrics_market_type', table_name='calibration_metrics')
    op.drop_index('ix_calibration_metrics_confidence_bucket', table_name='calibration_metrics')
    
    # Remove indexes from prediction_accuracy table
    op.drop_index('ix_prediction_accuracy_market_type', table_name='prediction_accuracy')
    op.drop_index('ix_prediction_accuracy_window_days', table_name='prediction_accuracy')
    
    # Remove indexes from rolling_accuracy table
    op.drop_index('ix_rolling_accuracy_market_type', table_name='rolling_accuracy')
    op.drop_index('ix_rolling_accuracy_window_days', table_name='rolling_accuracy')
    op.drop_index('ix_rolling_accuracy_date', table_name='rolling_accuracy')

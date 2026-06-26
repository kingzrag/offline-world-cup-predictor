"""Add prediction tracking and analytics tables

Revision ID: 20260627_0005
Revises: 20260626_0004
Create Date: 2026-06-27 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260627_0005"
down_revision: Union[str, None] = "20260626_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table_name: str) -> bool:
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


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

    # Create betting_market_predictions table
    if not _table_exists(conn, "betting_market_predictions"):
        op.create_table(
            "betting_market_predictions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("match_id", sa.Integer(), nullable=False),
            sa.Column("market_type", sa.String(length=50), nullable=False),
            sa.Column("predicted_value", sa.String(length=50), nullable=True),
            sa.Column("predicted_probability", sa.Float(), nullable=True),
            sa.Column("model_version", sa.String(length=50), nullable=False),
            sa.Column("source", sa.String(length=50), nullable=False),
            sa.Column("prediction_data", postgresql.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        )
        if not _index_exists(conn, "betting_market_predictions", "ix_betting_market_predictions_match_id"):
            op.create_index("ix_betting_market_predictions_match_id", "betting_market_predictions", ["match_id"])

    # Create prediction_accuracy table
    if not _table_exists(conn, "prediction_accuracy"):
        op.create_table(
            "prediction_accuracy",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("match_id", sa.Integer(), nullable=False),
            sa.Column("market_type", sa.String(length=50), nullable=False),
            sa.Column("predicted_value", sa.String(length=50), nullable=True),
            sa.Column("actual_value", sa.String(length=50), nullable=True),
            sa.Column("predicted_probability", sa.Float(), nullable=True),
            sa.Column("is_correct", sa.Boolean(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("model_version", sa.String(length=50), nullable=False),
            sa.Column("source", sa.String(length=50), nullable=False),
            sa.Column("match_date", sa.DateTime(), nullable=False),
            sa.Column("evaluated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
            sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        )
        if not _index_exists(conn, "prediction_accuracy", "ix_prediction_accuracy_match_id"):
            op.create_index("ix_prediction_accuracy_match_id", "prediction_accuracy", ["match_id"])

    # Create calibration_metrics table
    if not _table_exists(conn, "calibration_metrics"):
        op.create_table(
            "calibration_metrics",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("market_type", sa.String(length=50), nullable=False),
            sa.Column("confidence_bucket_min", sa.Float(), nullable=False),
            sa.Column("confidence_bucket_max", sa.Float(), nullable=False),
            sa.Column("total_predictions", sa.Integer(), nullable=False),
            sa.Column("correct_predictions", sa.Integer(), nullable=False),
            sa.Column("observed_frequency", sa.Float(), nullable=False),
            sa.Column("expected_frequency", sa.Float(), nullable=False),
            sa.Column("calculated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        )
        if not _index_exists(conn, "calibration_metrics", "ix_calibration_metrics_market_type"):
            op.create_index("ix_calibration_metrics_market_type", "calibration_metrics", ["market_type"])
        if not _index_exists(conn, "calibration_metrics", "ix_calibration_metrics_calculated_at"):
            op.create_index("ix_calibration_metrics_calculated_at", "calibration_metrics", ["calculated_at"])

    # Create rolling_accuracy table
    if not _table_exists(conn, "rolling_accuracy"):
        op.create_table(
            "rolling_accuracy",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("market_type", sa.String(length=50), nullable=False),
            sa.Column("window_days", sa.Integer(), nullable=False),
            sa.Column("total_predictions", sa.Integer(), nullable=False),
            sa.Column("correct_predictions", sa.Integer(), nullable=False),
            sa.Column("accuracy", sa.Float(), nullable=False),
            sa.Column("avg_confidence", sa.Float(), nullable=True),
            sa.Column("avg_log_loss", sa.Float(), nullable=True),
            sa.Column("calculated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        )
        if not _index_exists(conn, "rolling_accuracy", "ix_rolling_accuracy_market_type"):
            op.create_index("ix_rolling_accuracy_market_type", "rolling_accuracy", ["market_type"])
        if not _index_exists(conn, "rolling_accuracy", "ix_rolling_accuracy_calculated_at"):
            op.create_index("ix_rolling_accuracy_calculated_at", "rolling_accuracy", ["calculated_at"])


def downgrade() -> None:
    conn = op.get_bind()

    # Drop tables in reverse order
    if _table_exists(conn, "rolling_accuracy"):
        op.drop_table("rolling_accuracy")

    if _table_exists(conn, "calibration_metrics"):
        op.drop_table("calibration_metrics")

    if _table_exists(conn, "prediction_accuracy"):
        op.drop_table("prediction_accuracy")

    if _table_exists(conn, "betting_market_predictions"):
        op.drop_table("betting_market_predictions")

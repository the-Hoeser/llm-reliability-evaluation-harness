"""Persist confidence and abstention decisions for uncertainty experiments.

Revision ID: 0003_uncertainty_result_fields
Revises: 0002_model_endpoint
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_uncertainty_result_fields"
down_revision = "0002_model_endpoint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("test_results", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("test_results", sa.Column("abstained", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("test_results", "abstained")
    op.drop_column("test_results", "confidence")

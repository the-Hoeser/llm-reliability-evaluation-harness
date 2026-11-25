"""Add provider endpoint config and experiment system prompt.

Revision ID: 0002_model_endpoint
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_model_endpoint"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "model_configs",
        sa.Column(
            "endpoint_url",
            sa.String(length=500),
            nullable=False,
            server_default="https://api.openai.com/v1",
        ),
    )
    op.add_column(
        "model_configs",
        sa.Column(
            "api_key_env",
            sa.String(length=100),
            nullable=False,
            server_default="OPENAI_API_KEY",
        ),
    )
    op.add_column("experiments", sa.Column("system_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("experiments", "system_prompt")
    op.drop_column("model_configs", "api_key_env")
    op.drop_column("model_configs", "endpoint_url")

"""torna numero de serie opcional

Revision ID: 0014
Revises: 0013
"""

from alembic import op

from app.config import DATABASE_SCHEMA

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "patrimonios",
        "numero_serie",
        nullable=True,
        schema=DATABASE_SCHEMA,
    )


def downgrade() -> None:
    op.alter_column(
        "patrimonios",
        "numero_serie",
        nullable=False,
        schema=DATABASE_SCHEMA,
    )

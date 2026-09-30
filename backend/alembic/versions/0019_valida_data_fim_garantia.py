"""valida data de fim da garantia

Revision ID: 0019
Revises: 0018
"""

from alembic import op

from app.config import DATABASE_SCHEMA

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_patrimonios_garantia_data_cadastro",
        "patrimonios",
        "data_fim_garantia IS NULL OR "
        "data_fim_garantia >= "
        "(data_cadastro AT TIME ZONE 'America/Sao_Paulo')::date",
        schema=DATABASE_SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_patrimonios_garantia_data_cadastro",
        "patrimonios",
        schema=DATABASE_SCHEMA,
        type_="check",
    )

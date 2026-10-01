"""cria staging bigquery

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.config import DATABASE_SCHEMA

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


INDEX_COLUMNS = (
    "id",
    "tabela_origem",
    "codigo_protheus_consultado",
    "hash_registro",
    "usuario_id",
    "processado",
)


def upgrade() -> None:
    op.create_table(
        "integracao_bigquery_staging",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tabela_origem", sa.String(length=10), nullable=False),
        sa.Column("codigo_protheus_consultado", sa.String(length=100), nullable=False),
        sa.Column(
            "dados_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("hash_registro", sa.String(length=64), nullable=False),
        sa.Column(
            "consultado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column(
            "processado", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("processado_em", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "tabela_origem IN ('SN1', 'SN3', 'SNG')",
            name="ck_integracao_bigquery_staging_tabela_origem",
        ),
        sa.ForeignKeyConstraint(["usuario_id"], [f"{DATABASE_SCHEMA}.usuarios.id"]),
        schema=DATABASE_SCHEMA,
    )
    for coluna in INDEX_COLUMNS:
        op.create_index(
            f"ix_gadm_integracao_bigquery_staging_{coluna}",
            "integracao_bigquery_staging",
            [coluna],
            schema=DATABASE_SCHEMA,
        )


def downgrade() -> None:
    for coluna in reversed(INDEX_COLUMNS):
        op.drop_index(
            f"ix_gadm_integracao_bigquery_staging_{coluna}",
            table_name="integracao_bigquery_staging",
            schema=DATABASE_SCHEMA,
        )
    op.drop_table("integracao_bigquery_staging", schema=DATABASE_SCHEMA)

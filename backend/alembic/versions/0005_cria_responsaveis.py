"""cria responsaveis

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

from app.config import DATABASE_SCHEMA

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "responsaveis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo_re", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("cargo", sa.String(length=255), nullable=True),
        sa.Column("departamento_id", sa.Integer(), nullable=False),
        sa.Column("gestor_responsavel_id", sa.Integer(), nullable=True),
        sa.Column(
            "origem_dados",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'MANUAL'"),
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["departamento_id"], [f"{DATABASE_SCHEMA}.departamentos.id"]
        ),
        sa.ForeignKeyConstraint(
            ["gestor_responsavel_id"], [f"{DATABASE_SCHEMA}.responsaveis.id"]
        ),
        sa.UniqueConstraint("codigo_re", name="uq_responsaveis_codigo_re"),
        schema=DATABASE_SCHEMA,
    )
    for coluna in (
        "id",
        "codigo_re",
        "nome",
        "departamento_id",
        "gestor_responsavel_id",
    ):
        op.create_index(
            f"ix_gadm_responsaveis_{coluna}",
            "responsaveis",
            [coluna],
            schema=DATABASE_SCHEMA,
        )


def downgrade() -> None:
    for coluna in reversed(
        ("id", "codigo_re", "nome", "departamento_id", "gestor_responsavel_id")
    ):
        op.drop_index(
            f"ix_gadm_responsaveis_{coluna}",
            table_name="responsaveis",
            schema=DATABASE_SCHEMA,
        )
    op.drop_table("responsaveis", schema=DATABASE_SCHEMA)

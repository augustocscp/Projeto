"""cria usuarios e sessoes

Revision ID: 0001
Revises:
Create Date: 2026-09-21
"""

from alembic import op
import sqlalchemy as sa

from app.config import DATABASE_SCHEMA

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(f'CREATE SCHEMA IF NOT EXISTS "{DATABASE_SCHEMA}"')

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("azure_oid", sa.String(length=100), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("cargo", sa.String(length=100), nullable=False),
        sa.Column("filial", sa.String(length=100), nullable=False),
        sa.Column("perfil", sa.String(length=50), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("azure_oid"),
        sa.UniqueConstraint("email"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_usuarios_id", "usuarios", ["id"], schema=DATABASE_SCHEMA)
    op.create_index(
        "ix_gadm_usuarios_azure_oid",
        "usuarios",
        ["azure_oid"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_usuarios_email",
        "usuarios",
        ["email"],
        schema=DATABASE_SCHEMA,
    )

    op.create_table(
        "sessoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_acesso_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revogado_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            [f"{DATABASE_SCHEMA}.usuarios.id"],
        ),
        sa.UniqueConstraint("token_hash"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_sessoes_id", "sessoes", ["id"], schema=DATABASE_SCHEMA)
    op.create_index(
        "ix_gadm_sessoes_token_hash",
        "sessoes",
        ["token_hash"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_sessoes_usuario_id",
        "sessoes",
        ["usuario_id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_sessoes_expira_em",
        "sessoes",
        ["expira_em"],
        schema=DATABASE_SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_gadm_sessoes_expira_em", table_name="sessoes", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_sessoes_usuario_id", table_name="sessoes", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_sessoes_token_hash", table_name="sessoes", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_sessoes_id", table_name="sessoes", schema=DATABASE_SCHEMA)
    op.drop_table("sessoes", schema=DATABASE_SCHEMA)

    op.drop_index("ix_gadm_usuarios_email", table_name="usuarios", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_usuarios_azure_oid", table_name="usuarios", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_usuarios_id", table_name="usuarios", schema=DATABASE_SCHEMA)
    op.drop_table("usuarios", schema=DATABASE_SCHEMA)

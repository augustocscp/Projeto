"""adiciona item garantia e dados externos

Revision ID: 0009
Revises: 0008
"""

from alembic import op
import sqlalchemy as sa

from app.config import DATABASE_SCHEMA

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patrimonios", sa.Column("numero_item", sa.String(100), nullable=True), schema=DATABASE_SCHEMA)
    op.add_column("patrimonios", sa.Column("possui_garantia", sa.Boolean(), nullable=True), schema=DATABASE_SCHEMA)
    op.add_column("patrimonios", sa.Column("codigo_produto", sa.String(100), nullable=True), schema=DATABASE_SCHEMA)
    op.add_column("patrimonios", sa.Column("data_baixa_origem", sa.DateTime(timezone=True), nullable=True),
                  schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "codigo_protheus", nullable=False, schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "numero_item", nullable=False, schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "numero_serie", nullable=False, schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "possui_garantia", nullable=False, schema=DATABASE_SCHEMA)
    op.create_unique_constraint("uq_patrimonios_protheus_item", "patrimonios", ["codigo_protheus", "numero_item"],
                                schema=DATABASE_SCHEMA)
    op.create_check_constraint(
        "ck_patrimonios_garantia_data",
        "patrimonios",
        "(possui_garantia AND data_fim_garantia IS NOT NULL) OR (NOT possui_garantia AND data_fim_garantia IS NULL)",
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_patrimonios_numero_item", "patrimonios", ["numero_item"], schema=DATABASE_SCHEMA)

    op.add_column("responsaveis", sa.Column("departamento_externo", sa.String(255), nullable=True),
                  schema=DATABASE_SCHEMA)
    op.add_column("responsaveis", sa.Column("gestor_responsavel", sa.String(255), nullable=True),
                  schema=DATABASE_SCHEMA)
    op.add_column("responsaveis", sa.Column("consultado_em", sa.DateTime(timezone=True), nullable=True),
                  schema=DATABASE_SCHEMA)
    op.alter_column("responsaveis", "departamento_id", nullable=True, schema=DATABASE_SCHEMA)


def downgrade() -> None:
    op.alter_column("responsaveis", "departamento_id", nullable=False, schema=DATABASE_SCHEMA)
    for coluna in ("consultado_em", "gestor_responsavel", "departamento_externo"):
        op.drop_column("responsaveis", coluna, schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_patrimonios_numero_item", table_name="patrimonios", schema=DATABASE_SCHEMA)
    op.drop_constraint("ck_patrimonios_garantia_data", "patrimonios", schema=DATABASE_SCHEMA)
    op.drop_constraint("uq_patrimonios_protheus_item", "patrimonios", schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "possui_garantia", nullable=True, schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "numero_serie", nullable=True, schema=DATABASE_SCHEMA)
    op.alter_column("patrimonios", "codigo_protheus", nullable=True, schema=DATABASE_SCHEMA)
    for coluna in ("data_baixa_origem", "codigo_produto", "possui_garantia", "numero_item"):
        op.drop_column("patrimonios", coluna, schema=DATABASE_SCHEMA)

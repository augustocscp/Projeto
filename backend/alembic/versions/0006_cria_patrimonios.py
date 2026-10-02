"""cria patrimonios

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.config import DATABASE_SCHEMA

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

PATRIMONIO_NUMERO_TOMBO_SEQUENCE = sa.Sequence(
    "patrimonio_numero_tombo_seq",
    schema=DATABASE_SCHEMA,
)

INDEX_COLUMNS = (
    "id",
    "numero_tombo",
    "codigo_protheus",
    "codigo_sap",
    "numero_plaqueta_fisica",
    "numero_patrimonio_anterior",
    "categoria_id",
    "empresa_id",
    "filial_id",
    "departamento_id",
    "localizacao_id",
    "responsavel_id",
    "estado_conservacao_id",
    "situacao_id",
    "destinacao_id",
    "usuario_cadastro_id",
    "usuario_ultima_atualizacao_id",
)


def upgrade() -> None:
    PATRIMONIO_NUMERO_TOMBO_SEQUENCE.create(op.get_bind())
    op.create_table(
        "patrimonios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "numero_tombo",
            sa.String(length=30),
            nullable=False,
            server_default=PATRIMONIO_NUMERO_TOMBO_SEQUENCE.next_value(),
        ),
        sa.Column("codigo_protheus", sa.String(length=100), nullable=True),
        sa.Column("codigo_sap", sa.String(length=100), nullable=True),
        sa.Column("numero_plaqueta_fisica", sa.String(length=100), nullable=False),
        sa.Column("numero_patrimonio_anterior", sa.String(length=100), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("marca", sa.String(length=255), nullable=True),
        sa.Column("modelo", sa.String(length=255), nullable=True),
        sa.Column("fabricante", sa.String(length=255), nullable=True),
        sa.Column("numero_serie", sa.String(length=255), nullable=True),
        sa.Column("data_fim_garantia", sa.Date(), nullable=True),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("filial_id", sa.Integer(), nullable=False),
        sa.Column("departamento_id", sa.Integer(), nullable=False),
        sa.Column("localizacao_id", sa.Integer(), nullable=False),
        sa.Column("responsavel_id", sa.Integer(), nullable=False),
        sa.Column("estado_conservacao_id", sa.Integer(), nullable=False),
        sa.Column("situacao_id", sa.Integer(), nullable=False),
        sa.Column("destinacao_id", sa.Integer(), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("data_baixa", sa.Date(), nullable=True),
        sa.Column("usuario_cadastro_id", sa.Integer(), nullable=False),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("usuario_ultima_atualizacao_id", sa.Integer(), nullable=False),
        sa.Column(
            "data_ultima_atualizacao",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("protheus_status", sa.String(length=100), nullable=True),
        sa.Column("protheus_consultado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("protheus_atualizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dados_protheus_raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["categoria_id"], [f"{DATABASE_SCHEMA}.categorias_patrimoniais.id"]
        ),
        sa.ForeignKeyConstraint(["empresa_id"], [f"{DATABASE_SCHEMA}.empresas.id"]),
        sa.ForeignKeyConstraint(["filial_id"], [f"{DATABASE_SCHEMA}.filiais.id"]),
        sa.ForeignKeyConstraint(
            ["departamento_id"], [f"{DATABASE_SCHEMA}.departamentos.id"]
        ),
        sa.ForeignKeyConstraint(
            ["localizacao_id"], [f"{DATABASE_SCHEMA}.localizacoes.id"]
        ),
        sa.ForeignKeyConstraint(
            ["responsavel_id"], [f"{DATABASE_SCHEMA}.responsaveis.id"]
        ),
        sa.ForeignKeyConstraint(
            ["estado_conservacao_id"],
            [f"{DATABASE_SCHEMA}.estados_conservacao.id"],
        ),
        sa.ForeignKeyConstraint(
            ["situacao_id"], [f"{DATABASE_SCHEMA}.situacoes_patrimoniais.id"]
        ),
        sa.ForeignKeyConstraint(
            ["destinacao_id"], [f"{DATABASE_SCHEMA}.destinacoes_patrimoniais.id"]
        ),
        sa.ForeignKeyConstraint(
            ["usuario_cadastro_id"], [f"{DATABASE_SCHEMA}.usuarios.id"]
        ),
        sa.ForeignKeyConstraint(
            ["usuario_ultima_atualizacao_id"], [f"{DATABASE_SCHEMA}.usuarios.id"]
        ),
        sa.UniqueConstraint("numero_tombo", name="uq_patrimonios_numero_tombo"),
        sa.UniqueConstraint(
            "numero_plaqueta_fisica",
            name="uq_patrimonios_numero_plaqueta_fisica",
        ),
        schema=DATABASE_SCHEMA,
    )
    for coluna in INDEX_COLUMNS:
        op.create_index(
            f"ix_gadm_patrimonios_{coluna}",
            "patrimonios",
            [coluna],
            schema=DATABASE_SCHEMA,
        )


def downgrade() -> None:
    for coluna in reversed(INDEX_COLUMNS):
        op.drop_index(
            f"ix_gadm_patrimonios_{coluna}",
            table_name="patrimonios",
            schema=DATABASE_SCHEMA,
        )
    op.drop_table("patrimonios", schema=DATABASE_SCHEMA)
    PATRIMONIO_NUMERO_TOMBO_SEQUENCE.drop(op.get_bind())

"""cria patrimonios contabeis

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.config import DATABASE_SCHEMA

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("patrimonios_contabeis",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("patrimonio_id", sa.Integer(), nullable=False, unique=True),
                    sa.Column("numero_nota_fiscal", sa.String(100)), sa.Column("serie_nota_fiscal", sa.String(100)),
                    sa.Column("data_nota_fiscal", sa.Date()), sa.Column("codigo_fornecedor", sa.String(100)),
                    sa.Column("fornecedor", sa.String(255)), sa.Column("valor_aquisicao", sa.Numeric(18, 2)),
                    sa.Column("icms", sa.Numeric(18, 2)), sa.Column("valor_atual", sa.Numeric(18, 2)),
                    sa.Column("percentual_depreciacao", sa.Numeric(18, 6)),
                    sa.Column("depreciacao_mensal", sa.Numeric(18, 2)),
                    sa.Column("depreciacao_acumulada", sa.Numeric(18, 2)), sa.Column("inicio_depreciacao", sa.Date()),
                    sa.Column("fim_depreciacao", sa.Date()), sa.Column("conta_contabil", sa.String(100)),
                    sa.Column("centro_custo", sa.String(100)), sa.Column("data_baixa_sn1", sa.DateTime(timezone=True)),
                    sa.Column("data_baixa_sn3", sa.DateTime(timezone=True)),
                    sa.Column("consultado_em", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("dados_brutos_sn1", postgresql.JSONB(astext_type=sa.Text())),
                    sa.Column("dados_brutos_sn3", postgresql.JSONB(astext_type=sa.Text())),
                    sa.ForeignKeyConstraint(["patrimonio_id"], [f"{DATABASE_SCHEMA}.patrimonios.id"]),
                    schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_patrimonios_contabeis_patrimonio_id", "patrimonios_contabeis", ["patrimonio_id"],
                    schema=DATABASE_SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_gadm_patrimonios_contabeis_patrimonio_id", table_name="patrimonios_contabeis",
                  schema=DATABASE_SCHEMA)
    op.drop_table("patrimonios_contabeis", schema=DATABASE_SCHEMA)

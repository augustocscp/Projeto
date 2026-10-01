"""cria historico contabil

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa
from app.config import DATABASE_SCHEMA

revision = "0011";
down_revision = "0010";
branch_labels = None;
depends_on = None


def upgrade() -> None:
    op.create_table("historico_contabil", sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("patrimonio_id", sa.Integer(), nullable=False),
                    sa.Column("campo_alterado", sa.String(100), nullable=False),
                    sa.Column("valor_anterior", sa.Text()), sa.Column("valor_novo", sa.Text()),
                    sa.Column("origem", sa.String(20), nullable=False), sa.Column("usuario_id", sa.Integer()),
                    sa.Column("consultado_em", sa.DateTime(timezone=True), nullable=False),
                    sa.CheckConstraint("origem IN ('API', 'USUARIO')", name="ck_historico_contabil_origem"),
                    sa.ForeignKeyConstraint(["patrimonio_id"], [f"{DATABASE_SCHEMA}.patrimonios.id"]),
                    sa.ForeignKeyConstraint(["usuario_id"], [f"{DATABASE_SCHEMA}.usuarios.id"]), schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_historico_contabil_patrimonio_id", "historico_contabil", ["patrimonio_id"],
                    schema=DATABASE_SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_gadm_historico_contabil_patrimonio_id", table_name="historico_contabil", schema=DATABASE_SCHEMA);
    op.drop_table("historico_contabil", schema=DATABASE_SCHEMA)

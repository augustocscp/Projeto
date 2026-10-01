"""cria historico controle patrimonial

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa
from app.config import DATABASE_SCHEMA

revision = "0012";
down_revision = "0011";
branch_labels = None;
depends_on = None


def upgrade() -> None:
    op.create_table("historico_controle_patrimonial", sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("patrimonio_id", sa.Integer(), nullable=False),
                    sa.Column("campo_alterado", sa.String(100), nullable=False),
                    sa.Column("valor_anterior", sa.Text()), sa.Column("valor_novo", sa.Text()),
                    sa.Column("motivo", sa.Text()),
                    sa.Column("usuario_id", sa.Integer(), nullable=False),
                    sa.Column("data_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
                    sa.ForeignKeyConstraint(["patrimonio_id"], [f"{DATABASE_SCHEMA}.patrimonios.id"]),
                    sa.ForeignKeyConstraint(["usuario_id"], [f"{DATABASE_SCHEMA}.usuarios.id"]), schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_historico_controle_patrimonio_id", "historico_controle_patrimonial", ["patrimonio_id"],
                    schema=DATABASE_SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_gadm_historico_controle_patrimonio_id", table_name="historico_controle_patrimonial",
                  schema=DATABASE_SCHEMA);
    op.drop_table("historico_controle_patrimonial", schema=DATABASE_SCHEMA)

"""cria historico sistema

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.config import DATABASE_SCHEMA

revision = "0013";
down_revision = "0012";
branch_labels = None;
depends_on = None


def upgrade() -> None:
    op.create_table("historico_sistema", sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("patrimonio_id", sa.Integer()), sa.Column("tipo_evento", sa.String(50), nullable=False),
                    sa.Column("descricao", sa.Text(), nullable=False), sa.Column("usuario_id", sa.Integer()),
                    sa.Column("dados_contexto", postgresql.JSONB(astext_type=sa.Text())),
                    sa.Column("data_hora", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
                    sa.ForeignKeyConstraint(["patrimonio_id"], [f"{DATABASE_SCHEMA}.patrimonios.id"]),
                    sa.ForeignKeyConstraint(["usuario_id"], [f"{DATABASE_SCHEMA}.usuarios.id"]), schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_historico_sistema_patrimonio_id", "historico_sistema", ["patrimonio_id"],
                    schema=DATABASE_SCHEMA)
    op.execute(f"""
        CREATE FUNCTION {DATABASE_SCHEMA}.bloquear_mutacao_historico_sistema()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'historico_sistema e append-only';
        END;
        $$;
        CREATE TRIGGER trg_historico_sistema_append_only
        BEFORE UPDATE OR DELETE ON {DATABASE_SCHEMA}.historico_sistema
        FOR EACH ROW EXECUTE FUNCTION {DATABASE_SCHEMA}.bloquear_mutacao_historico_sistema();
    """)


def downgrade() -> None:
    op.execute(f"DROP TRIGGER trg_historico_sistema_append_only ON {DATABASE_SCHEMA}.historico_sistema")
    op.execute(f"DROP FUNCTION {DATABASE_SCHEMA}.bloquear_mutacao_historico_sistema()")
    op.drop_index("ix_gadm_historico_sistema_patrimonio_id", table_name="historico_sistema", schema=DATABASE_SCHEMA);
    op.drop_table("historico_sistema", schema=DATABASE_SCHEMA)

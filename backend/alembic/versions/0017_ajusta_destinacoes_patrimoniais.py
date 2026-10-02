"""ajusta destinacoes patrimoniais

Revision ID: 0017
Revises: 0016
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.config import DATABASE_SCHEMA

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def _tabelas():
    destinacoes = sa.table(
        "destinacoes_patrimoniais",
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.Text()),
        sa.column("ativo", sa.Boolean()),
        sa.column("ordem_exibicao", sa.Integer()),
        sa.column("atualizado_em", sa.DateTime(timezone=True)),
        schema=DATABASE_SCHEMA,
    )
    patrimonios = sa.table(
        "patrimonios",
        sa.column("destinacao_id", sa.Integer()),
        schema=DATABASE_SCHEMA,
    )
    return destinacoes, patrimonios


def upgrade() -> None:
    bind = op.get_bind()
    destinacoes, _ = _tabelas()

    bind.execute(
        sa.update(destinacoes)
        .where(destinacoes.c.codigo == "OPERACAO")
        .values(
            codigo="OPERACIONAL",
            nome="Operacional",
            ativo=True,
            atualizado_em=sa.func.now(),
        )
    )
    bind.execute(
        sa.update(destinacoes)
        .where(destinacoes.c.codigo == "ADMINISTRACAO")
        .values(
            codigo="ADMINISTRATIVO",
            nome="Administrativo",
            ativo=True,
            atualizado_em=sa.func.now(),
        )
    )
    selecao = sa.select(
        sa.literal("DOACAO"),
        sa.literal("Doação"),
        sa.null(),
        sa.true(),
        sa.func.coalesce(sa.func.max(destinacoes.c.ordem_exibicao), 0) + 1,
    ).select_from(destinacoes)
    comando = postgresql_insert(destinacoes).from_select(
        ["codigo", "nome", "descricao", "ativo", "ordem_exibicao"],
        selecao,
    )
    bind.execute(
        comando.on_conflict_do_update(
            index_elements=[destinacoes.c.codigo],
            set_={
                "nome": comando.excluded.nome,
                "ativo": True,
                "atualizado_em": sa.func.now(),
            },
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    destinacoes, patrimonios = _tabelas()

    bind.execute(
        sa.update(destinacoes)
        .where(destinacoes.c.codigo == "OPERACIONAL")
        .values(
            codigo="OPERACAO",
            nome="Operação",
            atualizado_em=sa.func.now(),
        )
    )
    bind.execute(
        sa.update(destinacoes)
        .where(destinacoes.c.codigo == "ADMINISTRATIVO")
        .values(
            codigo="ADMINISTRACAO",
            nome="Administração",
            atualizado_em=sa.func.now(),
        )
    )
    bind.execute(
        sa.delete(destinacoes).where(
            destinacoes.c.codigo == "DOACAO",
            ~sa.exists(
                sa.select(1).where(
                    patrimonios.c.destinacao_id == destinacoes.c.id
                )
            ),
        )
    )
    bind.execute(
        sa.update(destinacoes)
        .where(destinacoes.c.codigo == "DOACAO")
        .values(ativo=False, atualizado_em=sa.func.now())
    )

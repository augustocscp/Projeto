"""ajusta estados de conservacao para novos cadastros

Revision ID: 0016
Revises: 0015
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.config import DATABASE_SCHEMA

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def _aplicar_estados(estados: tuple[tuple[str, str], ...]) -> None:
    bind = op.get_bind()
    tabela = sa.table(
        "estados_conservacao",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.Text()),
        sa.column("ativo", sa.Boolean()),
        sa.column("ordem_exibicao", sa.Integer()),
        sa.column("atualizado_em", sa.DateTime(timezone=True)),
        schema=DATABASE_SCHEMA,
    )
    comando = postgresql_insert(tabela)
    comando = comando.on_conflict_do_update(
        index_elements=[tabela.c.codigo],
        set_={
            "nome": comando.excluded.nome,
            "ativo": True,
            "ordem_exibicao": comando.excluded.ordem_exibicao,
            "atualizado_em": sa.func.now(),
        },
    )
    bind.execute(
        comando,
        [
            {
                "codigo": codigo,
                "nome": nome,
                "descricao": None,
                "ativo": True,
                "ordem_exibicao": ordem,
            }
            for ordem, (codigo, nome) in enumerate(estados, start=1)
        ],
    )

    codigos = tuple(codigo for codigo, _ in estados)
    bind.execute(
        sa.update(tabela)
        .where(tabela.c.codigo.not_in(codigos))
        .values(ativo=False, atualizado_em=sa.func.now())
    )


def upgrade() -> None:
    _aplicar_estados(
        (
            ("OTIMO", "Ótimo"),
            ("BOM", "Bom"),
            ("REGULAR", "Regular"),
            ("RUIM", "Ruim"),
            ("DANIFICADO", "Danificado"),
            ("NAO_AVALIADO", "Não avaliado"),
        )
    )


def downgrade() -> None:
    _aplicar_estados(
        (
            ("NOVO", "Novo"),
            ("OTIMO", "Ótimo"),
            ("BOM", "Bom"),
            ("REGULAR", "Regular"),
            ("RUIM", "Ruim"),
            ("INSERVIVEL", "Inservível"),
        )
    )

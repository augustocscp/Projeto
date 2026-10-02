"""move coordenacao para o escritorio matriz

Revision ID: 0015
Revises: 0014
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.config import DATABASE_SCHEMA

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def _mover_vinculos(nome_filial_destino: str, manter_departamento: str) -> None:
    bind = op.get_bind()
    empresas = sa.table(
        "empresas",
        sa.column("id", sa.Integer()),
        sa.column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    filiais = sa.table(
        "filiais",
        sa.column("id", sa.Integer()),
        sa.column("empresa_id", sa.Integer()),
        sa.column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    localizacoes = sa.table(
        "localizacoes",
        sa.column("id", sa.Integer()),
        sa.column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    departamentos = sa.table(
        "departamentos",
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    vinculos = sa.table(
        "localizacao_vinculos",
        sa.column("localizacao_id", sa.Integer()),
        sa.column("filial_id", sa.Integer()),
        sa.column("departamento_id", sa.Integer()),
        sa.column("ativo", sa.Boolean()),
        sa.column("criado_em", sa.DateTime(timezone=True)),
        sa.column("atualizado_em", sa.DateTime(timezone=True)),
        schema=DATABASE_SCHEMA,
    )
    patrimonios = sa.table(
        "patrimonios",
        sa.column("filial_id", sa.Integer()),
        sa.column("departamento_id", sa.Integer()),
        sa.column("localizacao_id", sa.Integer()),
        sa.column("data_ultima_atualizacao", sa.DateTime(timezone=True)),
        schema=DATABASE_SCHEMA,
    )

    filial_destino = (
        sa.select(filiais.c.id)
        .join(empresas, empresas.c.id == filiais.c.empresa_id)
        .where(
            empresas.c.nome.ilike("Urbi mobilidade"),
            filiais.c.nome.ilike(f"%{nome_filial_destino}%"),
        )
        .limit(1)
        .cte("filial_destino")
    )
    vinculos_destino = (
        sa.select(
            vinculos.c.localizacao_id,
            filial_destino.c.id.label("filial_id"),
            vinculos.c.departamento_id,
            sa.func.bool_or(vinculos.c.ativo).label("ativo"),
            sa.func.min(vinculos.c.criado_em).label("criado_em"),
            sa.func.now().label("atualizado_em"),
        )
        .join(localizacoes, localizacoes.c.id == vinculos.c.localizacao_id)
        .join(departamentos, departamentos.c.id == vinculos.c.departamento_id)
        .join(filial_destino, sa.true())
        .where(
            localizacoes.c.nome.ilike("COORDENA%"),
            departamentos.c.codigo != manter_departamento,
        )
        .group_by(
            vinculos.c.localizacao_id,
            filial_destino.c.id,
            vinculos.c.departamento_id,
        )
        .cte("vinculos_destino")
    )
    comando = postgresql_insert(vinculos).from_select(
        [
            "localizacao_id",
            "filial_id",
            "departamento_id",
            "ativo",
            "criado_em",
            "atualizado_em",
        ],
        sa.select(vinculos_destino),
    )
    bind.execute(
        comando.on_conflict_do_update(
            index_elements=[
                vinculos.c.localizacao_id,
                vinculos.c.filial_id,
                vinculos.c.departamento_id,
            ],
            set_={
                "ativo": comando.excluded.ativo,
                "atualizado_em": sa.func.now(),
            },
        )
    )

    destino_id = sa.select(filial_destino.c.id).scalar_subquery()
    localizacoes_coordenacao = sa.select(localizacoes.c.id).where(
        localizacoes.c.nome.ilike("COORDENA%")
    )
    departamento_movivel = sa.exists(
        sa.select(1).where(
            departamentos.c.id == patrimonios.c.departamento_id,
            departamentos.c.codigo != manter_departamento,
        )
    )
    bind.execute(
        sa.update(patrimonios)
        .where(
            patrimonios.c.localizacao_id.in_(localizacoes_coordenacao),
            patrimonios.c.filial_id != destino_id,
            departamento_movivel,
        )
        .values(filial_id=destino_id, data_ultima_atualizacao=sa.func.now())
    )

    bind.execute(
        sa.delete(vinculos).where(
            vinculos.c.localizacao_id.in_(localizacoes_coordenacao),
            vinculos.c.filial_id != destino_id,
            sa.exists(
                sa.select(1).where(
                    departamentos.c.id == vinculos.c.departamento_id,
                    departamentos.c.codigo != manter_departamento,
                )
            ),
        )
    )


def upgrade() -> None:
    _mover_vinculos("matriz", "")


def downgrade() -> None:
    _mover_vinculos("Samambaia", "GSMA")

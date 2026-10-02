"""cria dominios patrimoniais

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.config import DATABASE_SCHEMA

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

DOMINIOS = {
    "estados_conservacao": (
        ("OTIMO", "Ótimo"),
        ("BOM", "Bom"),
        ("REGULAR", "Regular"),
        ("RUIM", "Ruim"),
        ("DANIFICADO", "Danificado"),
        ("NAO_AVALIADO", "Não avaliado"),
    ),
    "situacoes_patrimoniais": (
        ("EM_USO", "Em uso"),
        ("DISPONIVEL", "Disponível"),
        ("EM_MANUTENCAO", "Em manutenção"),
        ("RESERVA", "Reserva"),
        ("EXTRAVIADO", "Extraviado"),
        ("BAIXADO", "Baixado"),
    ),
    "destinacoes_patrimoniais": (
        ("USO_INTERNO", "Uso interno"),
        ("COMODATO", "Comodato"),
        ("DOACAO", "Doação"),
        ("VENDA", "Venda"),
        ("TRANSFERENCIA", "Transferência"),
        ("SUCATA_DESCARTE", "Sucata/Descarte"),
    ),
}


def _criar_tabela_dominio(nome: str) -> None:
    op.create_table(
        nome,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("ordem_exibicao", sa.Integer(), nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("codigo", name=f"uq_{nome}_codigo"),
        sa.UniqueConstraint("nome", name=f"uq_{nome}_nome"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index(f"ix_gadm_{nome}_id", nome, ["id"], schema=DATABASE_SCHEMA)
    op.create_index(f"ix_gadm_{nome}_codigo", nome, ["codigo"], schema=DATABASE_SCHEMA)
    op.create_index(f"ix_gadm_{nome}_nome", nome, ["nome"], schema=DATABASE_SCHEMA)


def _seed_dominios() -> None:
    bind = op.get_bind()
    for tabela, registros in DOMINIOS.items():
        dominio = sa.table(
            tabela,
            sa.column("codigo", sa.String()),
            sa.column("nome", sa.String()),
            sa.column("descricao", sa.Text()),
            sa.column("ativo", sa.Boolean()),
            sa.column("ordem_exibicao", sa.Integer()),
            sa.column("atualizado_em", sa.DateTime(timezone=True)),
            schema=DATABASE_SCHEMA,
        )
        comando = postgresql_insert(dominio).values(
            descricao=None,
            ativo=True,
        )
        comando = comando.on_conflict_do_update(
            index_elements=[dominio.c.codigo],
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
                {"codigo": codigo, "nome": nome, "ordem_exibicao": ordem}
                for ordem, (codigo, nome) in enumerate(registros, start=1)
            ],
        )


def upgrade() -> None:
    op.create_table(
        "categorias_patrimoniais",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("codigo", name="uq_categorias_patrimoniais_codigo"),
        sa.UniqueConstraint("nome", name="uq_categorias_patrimoniais_nome"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_categorias_patrimoniais_id",
        "categorias_patrimoniais",
        ["id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_categorias_patrimoniais_codigo",
        "categorias_patrimoniais",
        ["codigo"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_categorias_patrimoniais_nome",
        "categorias_patrimoniais",
        ["nome"],
        schema=DATABASE_SCHEMA,
    )

    for tabela in DOMINIOS:
        _criar_tabela_dominio(tabela)
    _seed_dominios()


def downgrade() -> None:
    for tabela in reversed(tuple(DOMINIOS)):
        op.drop_index(f"ix_gadm_{tabela}_nome", table_name=tabela, schema=DATABASE_SCHEMA)
        op.drop_index(f"ix_gadm_{tabela}_codigo", table_name=tabela, schema=DATABASE_SCHEMA)
        op.drop_index(f"ix_gadm_{tabela}_id", table_name=tabela, schema=DATABASE_SCHEMA)
        op.drop_table(tabela, schema=DATABASE_SCHEMA)

    op.drop_index(
        "ix_gadm_categorias_patrimoniais_nome",
        table_name="categorias_patrimoniais",
        schema=DATABASE_SCHEMA,
    )
    op.drop_index(
        "ix_gadm_categorias_patrimoniais_codigo",
        table_name="categorias_patrimoniais",
        schema=DATABASE_SCHEMA,
    )
    op.drop_index(
        "ix_gadm_categorias_patrimoniais_id",
        table_name="categorias_patrimoniais",
        schema=DATABASE_SCHEMA,
    )
    op.drop_table("categorias_patrimoniais", schema=DATABASE_SCHEMA)

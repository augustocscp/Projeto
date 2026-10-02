"""ajusta estrutura das tabelas cadastrais

Revision ID: 0018
Revises: 0017
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.config import DATABASE_SCHEMA

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

DEPARTAMENTOS = {
    1: "Diretoria colegiada",
    2: "Departamento pessoal",
    3: "Gestão administrativa",
    4: "Gente e cultura",
    5: "Gestão de desempenho",
    6: "Gestão de inteligência e performance",
    7: "Gestão de marketing",
    8: "Gestão de operações",
    9: "Gestão de planejamento, qualidade e serviço",
    10: "Gestão de performance veicular",
    11: "Gestão de risco e contratos",
    12: "Gerência de pessoas e suporte ao negócio",
    13: "Gestão de saúde e meio ambiente",
    14: "Gestão de sinistros e operações de relacionamento",
    15: "Gestão de suprimento",
    16: "Gerência de transporte e relacionamento",
    17: "Gestão de tecnologia e serviço da inteligência",
}

DOMINIO_FKS = {
    "estados_conservacao": "estado_conservacao_id",
    "situacoes_patrimoniais": "situacao_id",
}


def _dominio(nome: str):
    if nome not in DOMINIO_FKS:
        raise ValueError(f"Dominio nao permitido: {nome}")
    return sa.table(
        nome,
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        schema=DATABASE_SCHEMA,
    )


def _remapear_e_excluir(
        tabela_dominio: str,
        coluna_fk: str,
        codigos_excluidos: tuple[str, ...],
        codigo_destino: str,
) -> None:
    if DOMINIO_FKS.get(tabela_dominio) != coluna_fk:
        raise ValueError("Combinacao de dominio e chave estrangeira nao permitida")
    bind = op.get_bind()
    dominio = _dominio(tabela_dominio)
    patrimonios = sa.table(
        "patrimonios",
        sa.column(coluna_fk, sa.Integer()),
        schema=DATABASE_SCHEMA,
    )
    ids_origem = sa.select(dominio.c.id).where(
        dominio.c.codigo.in_(codigos_excluidos)
    )
    id_destino = sa.select(dominio.c.id).where(
        dominio.c.codigo == codigo_destino
    ).scalar_subquery()
    bind.execute(
        sa.update(patrimonios)
        .where(patrimonios.c[coluna_fk].in_(ids_origem))
        .values({coluna_fk: id_destino})
    )
    bind.execute(
        sa.delete(dominio).where(dominio.c.codigo.in_(codigos_excluidos))
    )


def upgrade() -> None:
    bind = op.get_bind()
    departamentos = sa.table(
        "departamentos",
        sa.column("id", sa.Integer()),
        sa.column("descricao", sa.Text()),
        sa.column("atualizado_em", sa.DateTime(timezone=True)),
        schema=DATABASE_SCHEMA,
    )
    for departamento_id, descricao in DEPARTAMENTOS.items():
        bind.execute(
            sa.update(departamentos)
            .where(departamentos.c.id == departamento_id)
            .values(descricao=descricao, atualizado_em=sa.func.now())
        )

    _remapear_e_excluir(
        "estados_conservacao",
        "estado_conservacao_id",
        ("NOVO", "INSERVIVEL"),
        "NAO_AVALIADO",
    )
    _remapear_e_excluir(
        "situacoes_patrimoniais",
        "situacao_id",
        ("ATIVO", "EM_TRANSFERENCIA"),
        "EM_USO",
    )

    op.drop_index(
        "ix_gadm_categorias_patrimoniais_codigo",
        table_name="categorias_patrimoniais",
        schema=DATABASE_SCHEMA,
    )
    op.drop_constraint(
        "uq_categorias_patrimoniais_codigo",
        "categorias_patrimoniais",
        schema=DATABASE_SCHEMA,
        type_="unique",
    )
    op.drop_column("categorias_patrimoniais", "codigo", schema=DATABASE_SCHEMA)
    op.drop_column("categorias_patrimoniais", "descricao", schema=DATABASE_SCHEMA)

    op.drop_column("cidades", "codigo_ibge", schema=DATABASE_SCHEMA)

    op.drop_index(
        "ix_gadm_departamentos_codigo",
        table_name="departamentos",
        schema=DATABASE_SCHEMA,
    )
    op.drop_constraint(
        "uq_departamentos_codigo",
        "departamentos",
        schema=DATABASE_SCHEMA,
        type_="unique",
    )
    op.drop_column("departamentos", "codigo", schema=DATABASE_SCHEMA)

    op.drop_index(
        "ix_gadm_destinacoes_patrimoniais_codigo",
        table_name="destinacoes_patrimoniais",
        schema=DATABASE_SCHEMA,
    )
    op.drop_constraint(
        "uq_destinacoes_patrimoniais_codigo",
        "destinacoes_patrimoniais",
        schema=DATABASE_SCHEMA,
        type_="unique",
    )
    op.drop_column("destinacoes_patrimoniais", "codigo", schema=DATABASE_SCHEMA)
    op.drop_column("destinacoes_patrimoniais", "descricao", schema=DATABASE_SCHEMA)

    op.drop_column("empresas", "descricao", schema=DATABASE_SCHEMA)
    op.drop_column("estados_conservacao", "descricao", schema=DATABASE_SCHEMA)
    op.drop_column("filiais", "codigo", schema=DATABASE_SCHEMA)


def downgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "filiais", sa.Column("codigo", sa.String(length=20), nullable=True), schema=DATABASE_SCHEMA
    )
    op.add_column(
        "estados_conservacao", sa.Column("descricao", sa.Text(), nullable=True), schema=DATABASE_SCHEMA
    )
    op.add_column(
        "empresas", sa.Column("descricao", sa.Text(), nullable=True), schema=DATABASE_SCHEMA
    )

    op.add_column(
        "destinacoes_patrimoniais", sa.Column("descricao", sa.Text(), nullable=True), schema=DATABASE_SCHEMA
    )
    op.add_column(
        "destinacoes_patrimoniais", sa.Column("codigo", sa.String(length=50), nullable=True), schema=DATABASE_SCHEMA
    )
    destinacoes = sa.table(
        "destinacoes_patrimoniais",
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    bind.execute(
        sa.update(destinacoes).values(
            codigo=sa.literal("DESTINACAO_") + sa.cast(destinacoes.c.id, sa.String())
        )
    )
    op.alter_column(
        "destinacoes_patrimoniais", "codigo", nullable=False, schema=DATABASE_SCHEMA
    )
    op.create_unique_constraint(
        "uq_destinacoes_patrimoniais_codigo",
        "destinacoes_patrimoniais",
        ["codigo"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_destinacoes_patrimoniais_codigo",
        "destinacoes_patrimoniais",
        ["codigo"],
        schema=DATABASE_SCHEMA,
    )

    op.add_column(
        "departamentos", sa.Column("codigo", sa.String(length=20), nullable=True), schema=DATABASE_SCHEMA
    )
    departamentos = sa.table(
        "departamentos",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    bind.execute(sa.update(departamentos).values(codigo=departamentos.c.nome))
    op.alter_column("departamentos", "codigo", nullable=False, schema=DATABASE_SCHEMA)
    op.create_unique_constraint(
        "uq_departamentos_codigo", "departamentos", ["codigo"], schema=DATABASE_SCHEMA
    )
    op.create_index(
        "ix_gadm_departamentos_codigo",
        "departamentos",
        ["codigo"],
        schema=DATABASE_SCHEMA,
    )

    op.add_column(
        "cidades", sa.Column("codigo_ibge", sa.String(length=20), nullable=True), schema=DATABASE_SCHEMA
    )

    op.add_column(
        "categorias_patrimoniais", sa.Column("descricao", sa.Text(), nullable=True), schema=DATABASE_SCHEMA
    )
    op.add_column(
        "categorias_patrimoniais", sa.Column("codigo", sa.String(length=50), nullable=True), schema=DATABASE_SCHEMA
    )
    categorias = sa.table(
        "categorias_patrimoniais",
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    bind.execute(
        sa.update(categorias).values(
            codigo=sa.literal("CATEGORIA_") + sa.cast(categorias.c.id, sa.String())
        )
    )
    op.alter_column(
        "categorias_patrimoniais", "codigo", nullable=False, schema=DATABASE_SCHEMA
    )
    op.create_unique_constraint(
        "uq_categorias_patrimoniais_codigo",
        "categorias_patrimoniais",
        ["codigo"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_categorias_patrimoniais_codigo",
        "categorias_patrimoniais",
        ["codigo"],
        schema=DATABASE_SCHEMA,
    )

    estados = sa.table(
        "estados_conservacao",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.Text()),
        sa.column("ativo", sa.Boolean()),
        sa.column("ordem_exibicao", sa.Integer()),
        schema=DATABASE_SCHEMA,
    )
    for codigo, nome, ativo, ordem in (
            ("NOVO", "Novo", False, 1),
            ("INSERVIVEL", "Inservível", False, 6),
    ):
        bind.execute(
            postgresql_insert(estados)
            .values(
                codigo=codigo,
                nome=nome,
                descricao=None,
                ativo=ativo,
                ordem_exibicao=ordem,
            )
            .on_conflict_do_nothing(index_elements=[estados.c.codigo])
        )
    situacoes = sa.table(
        "situacoes_patrimoniais",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.Text()),
        sa.column("ativo", sa.Boolean()),
        sa.column("ordem_exibicao", sa.Integer()),
        schema=DATABASE_SCHEMA,
    )
    for codigo, nome, ordem in (
            ("ATIVO", "Ativo", 1),
            ("EM_TRANSFERENCIA", "Em Transferência", 5),
    ):
        bind.execute(
            postgresql_insert(situacoes)
            .values(
                codigo=codigo,
                nome=nome,
                descricao=None,
                ativo=True,
                ordem_exibicao=ordem,
            )
            .on_conflict_do_nothing(index_elements=[situacoes.c.codigo])
        )

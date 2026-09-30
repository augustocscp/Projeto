"""ajusta estrutura das tabelas cadastrais

Revision ID: 0018
Revises: 0017
"""

from alembic import op
import sqlalchemy as sa

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


def _remapear_e_excluir(
    tabela_dominio: str,
    coluna_fk: str,
    codigos_excluidos: tuple[str, ...],
    codigo_destino: str,
) -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.patrimonios patrimonio
            SET {coluna_fk} = destino.id
            FROM {DATABASE_SCHEMA}.{tabela_dominio} origem,
                 {DATABASE_SCHEMA}.{tabela_dominio} destino
            WHERE patrimonio.{coluna_fk} = origem.id
              AND origem.codigo IN :codigos
              AND destino.codigo = :codigo_destino
            """
        ).bindparams(sa.bindparam("codigos", expanding=True)),
        {"codigos": codigos_excluidos, "codigo_destino": codigo_destino},
    )
    bind.execute(
        sa.text(
            f"""
            DELETE FROM {DATABASE_SCHEMA}.{tabela_dominio}
            WHERE codigo IN :codigos
            """
        ).bindparams(sa.bindparam("codigos", expanding=True)),
        {"codigos": codigos_excluidos},
    )


def upgrade() -> None:
    bind = op.get_bind()
    for departamento_id, descricao in DEPARTAMENTOS.items():
        bind.execute(
            sa.text(
                f"""
                UPDATE {DATABASE_SCHEMA}.departamentos
                SET descricao = :descricao,
                    atualizado_em = now()
                WHERE id = :departamento_id
                """
            ),
            {"departamento_id": departamento_id, "descricao": descricao},
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
    op.execute(
        f"UPDATE {DATABASE_SCHEMA}.destinacoes_patrimoniais "
        "SET codigo = 'DESTINACAO_' || id"
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
    op.execute(f"UPDATE {DATABASE_SCHEMA}.departamentos SET codigo = nome")
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
    op.execute(
        f"UPDATE {DATABASE_SCHEMA}.categorias_patrimoniais "
        "SET codigo = 'CATEGORIA_' || id"
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

    bind = op.get_bind()
    for codigo, nome, ativo, ordem in (
        ("NOVO", "Novo", False, 1),
        ("INSERVIVEL", "Inservível", False, 6),
    ):
        bind.execute(
            sa.text(
                f"""
                INSERT INTO {DATABASE_SCHEMA}.estados_conservacao
                    (codigo, nome, descricao, ativo, ordem_exibicao)
                VALUES (:codigo, :nome, NULL, :ativo, :ordem)
                ON CONFLICT (codigo) DO NOTHING
                """
            ),
            {"codigo": codigo, "nome": nome, "ativo": ativo, "ordem": ordem},
        )
    for codigo, nome, ordem in (
        ("ATIVO", "Ativo", 1),
        ("EM_TRANSFERENCIA", "Em Transferência", 5),
    ):
        bind.execute(
            sa.text(
                f"""
                INSERT INTO {DATABASE_SCHEMA}.situacoes_patrimoniais
                    (codigo, nome, descricao, ativo, ordem_exibicao)
                VALUES (:codigo, :nome, NULL, true, :ordem)
                ON CONFLICT (codigo) DO NOTHING
                """
            ),
            {"codigo": codigo, "nome": nome, "ordem": ordem},
        )

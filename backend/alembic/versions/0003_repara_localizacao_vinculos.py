"""repara tabela e dados de vinculos das localizacoes

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unicodedata

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from app.config import DATABASE_SCHEMA

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _carregar_vinculos() -> tuple[tuple[str, str, str], ...]:
    """Reutiliza a carga historica preservada na revisao que a originou."""
    migration_path = Path(__file__).with_name(
        "0002_cria_estrutura_organizacional_e_localizacoes.py"
    )
    spec = spec_from_file_location("migration_0002_localizacoes", migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar os vinculos de {migration_path}")

    migration_0002 = module_from_spec(spec)
    spec.loader.exec_module(migration_0002)
    vinculos = tuple(migration_0002.LOCALIZACAO_VINCULOS)

    if len(vinculos) != 172 or len(set(vinculos)) != 172:
        raise RuntimeError(
            "A carga historica deve conter exatamente 172 vinculos distintos"
        )
    return vinculos


def _criar_tabela_se_ausente() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("localizacao_vinculos", schema=DATABASE_SCHEMA):
        return

    op.create_table(
        "localizacao_vinculos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("localizacao_id", sa.Integer(), nullable=False),
        sa.Column("filial_id", sa.Integer(), nullable=False),
        sa.Column("departamento_id", sa.Integer(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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
        sa.ForeignKeyConstraint(
            ["localizacao_id"],
            [f"{DATABASE_SCHEMA}.localizacoes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["filial_id"],
            [f"{DATABASE_SCHEMA}.filiais.id"],
        ),
        sa.ForeignKeyConstraint(
            ["departamento_id"],
            [f"{DATABASE_SCHEMA}.departamentos.id"],
        ),
        sa.UniqueConstraint(
            "localizacao_id",
            "filial_id",
            "departamento_id",
            name="uq_localizacao_vinculos_localizacao_filial_departamento",
        ),
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_id",
        "localizacao_vinculos",
        ["id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_localizacao_id",
        "localizacao_vinculos",
        ["localizacao_id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_filial_id",
        "localizacao_vinculos",
        ["filial_id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_departamento_id",
        "localizacao_vinculos",
        ["departamento_id"],
        schema=DATABASE_SCHEMA,
    )


def _normalizar_nome(nome: str) -> str:
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", nome)
        if not unicodedata.combining(caractere)
    )
    return " ".join(sem_acentos.casefold().split())


def _classificar_tipo_localizacao(nome: str) -> str:
    prefixos = (
        ("SALA", "SALA"),
        ("PATIO", "PATIO"),
        ("TERMINAL", "TERMINAL"),
        ("PORTAO", "PORTAO"),
        ("PORTARIA", "PORTAO"),
        ("GUARITA", "PORTAO"),
        ("BANHEIRO", "BANHEIRO"),
        ("ESTACIONAMENTO", "ESTACIONAMENTO"),
        ("DEPOSITO", "DEPOSITO"),
        ("ALMOXARIFADO", "DEPOSITO"),
    )
    nome_normalizado = _normalizar_nome(nome).upper()
    for prefixo, tipo in prefixos:
        if nome_normalizado.startswith(prefixo):
            return tipo
    return "OUTRO"


def _mapa_unico(rows, entidade: str) -> dict[str, int]:
    resultado: dict[str, int] = {}
    for identificador, nome in rows:
        nome_normalizado = _normalizar_nome(nome)
        if nome_normalizado in resultado and resultado[nome_normalizado] != identificador:
            raise RuntimeError(
                f"Existem dois registros equivalentes em {entidade}: {nome!r}"
            )
        resultado[nome_normalizado] = identificador
    return resultado


def _preparar_schema_localizacoes() -> None:
    colunas = {
        coluna["name"]
        for coluna in sa.inspect(op.get_bind()).get_columns(
            "localizacoes",
            schema=DATABASE_SCHEMA,
        )
    }
    for coluna in ("filial_id", "departamento_id"):
        if coluna in colunas:
            op.alter_column(
                "localizacoes",
                coluna,
                existing_type=sa.Integer(),
                nullable=True,
                schema=DATABASE_SCHEMA,
            )


def _garantir_localizacoes(
        vinculos: tuple[tuple[str, str, str], ...],
) -> dict[str, int]:
    bind = op.get_bind()
    tabela = sa.table(
        "localizacoes",
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("tipo", sa.String()),
        sa.column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )
    localizacoes = _mapa_unico(
        bind.execute(sa.select(tabela.c.id, tabela.c.nome)).all(),
        "localizacoes",
    )
    nomes_esperados = sorted({localizacao for localizacao, _, _ in vinculos})
    ausentes = [
        nome
        for nome in nomes_esperados
        if _normalizar_nome(nome) not in localizacoes
    ]
    if ausentes:
        bind.execute(
            sa.insert(tabela),
            [
                {
                    "codigo": None,
                    "nome": nome,
                    "tipo": _classificar_tipo_localizacao(nome),
                    "ativo": True,
                }
                for nome in ausentes
            ],
        )

    return _mapa_unico(
        bind.execute(sa.select(tabela.c.id, tabela.c.nome)).all(),
        "localizacoes",
    )


def _resolver_referencias(
        vinculos: tuple[tuple[str, str, str], ...],
) -> list[dict[str, int]]:
    bind = op.get_bind()
    localizacoes = _garantir_localizacoes(vinculos)

    filiais_tabela = sa.table(
        "filiais",
        sa.column("id", sa.Integer()),
        sa.column("empresa_id", sa.Integer()),
        sa.column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    empresas = sa.table(
        "empresas",
        sa.column("id", sa.Integer()),
        sa.column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    departamentos_tabela = sa.table(
        "departamentos",
        sa.column("id", sa.Integer()),
        sa.column("codigo", sa.String()),
        schema=DATABASE_SCHEMA,
    )

    filial_rows = bind.execute(
        sa.select(
            filiais_tabela.c.id,
            filiais_tabela.c.nome,
            empresas.c.nome.label("empresa_nome"),
        ).join(
            empresas,
            empresas.c.id == filiais_tabela.c.empresa_id,
        )
    ).all()
    filiais = _mapa_unico(
        [
            (identificador, nome)
            for identificador, nome, empresa_nome in filial_rows
            if _normalizar_nome(empresa_nome) == "urbi mobilidade"
        ],
        "filiais da Urbi Mobilidade",
    )
    departamentos = {
        codigo.upper(): identificador
        for identificador, codigo in bind.execute(
            sa.select(departamentos_tabela.c.id, departamentos_tabela.c.codigo)
        ).all()
    }

    faltantes: list[tuple[str, str, str]] = []
    registros: list[dict[str, int]] = []
    for localizacao, filial, departamento in vinculos:
        localizacao_id = localizacoes.get(_normalizar_nome(localizacao))
        filial_id = filiais.get(_normalizar_nome(filial))
        departamento_id = departamentos.get(departamento.upper())
        if localizacao_id is None or filial_id is None or departamento_id is None:
            faltantes.append((localizacao, filial, departamento))
            continue
        registros.append(
            {
                "localizacao_id": localizacao_id,
                "filial_id": filial_id,
                "departamento_id": departamento_id,
            }
        )

    if faltantes:
        exemplos = ", ".join(repr(item) for item in faltantes[:5])
        raise RuntimeError(
            f"Existem {len(faltantes)} vinculos com referencias ausentes: {exemplos}"
        )
    return registros


def _inserir_vinculos(registros: list[dict[str, int]]) -> None:
    tabela = sa.table(
        "localizacao_vinculos",
        sa.column("localizacao_id", sa.Integer()),
        sa.column("filial_id", sa.Integer()),
        sa.column("departamento_id", sa.Integer()),
        sa.column("ativo", sa.Boolean()),
        sa.column("atualizado_em", sa.DateTime(timezone=True)),
        schema=DATABASE_SCHEMA,
    )
    comando = postgresql_insert(tabela).values(ativo=True)
    comando = comando.on_conflict_do_update(
        index_elements=[
            tabela.c.localizacao_id,
            tabela.c.filial_id,
            tabela.c.departamento_id,
        ],
        set_={"ativo": True, "atualizado_em": sa.func.now()},
    )
    op.get_bind().execute(comando, registros)


def _validar_resultado(registros: list[dict[str, int]]) -> None:
    tabela = sa.table(
        "localizacao_vinculos",
        sa.column("localizacao_id", sa.Integer()),
        sa.column("filial_id", sa.Integer()),
        sa.column("departamento_id", sa.Integer()),
        schema=DATABASE_SCHEMA,
    )
    existentes = set(
        op.get_bind().execute(
            sa.select(
                tabela.c.localizacao_id,
                tabela.c.filial_id,
                tabela.c.departamento_id,
            )
        ).tuples()
    )
    esperados = {
        (
            registro["localizacao_id"],
            registro["filial_id"],
            registro["departamento_id"],
        )
        for registro in registros
    }
    faltantes = esperados - existentes
    if len(esperados) != 172 or faltantes:
        raise RuntimeError(
            f"Foram encontrados {172 - len(faltantes)} dos 172 vinculos esperados"
        )


def _finalizar_schema_localizacoes() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    colunas = {
        coluna["name"]
        for coluna in inspector.get_columns(
            "localizacoes",
            schema=DATABASE_SCHEMA,
        )
    }
    colunas_legadas = {"filial_id", "departamento_id"} & colunas

    if colunas_legadas:
        for restricao in inspector.get_unique_constraints(
                "localizacoes",
                schema=DATABASE_SCHEMA,
        ):
            if colunas_legadas & set(restricao["column_names"]):
                op.drop_constraint(
                    restricao["name"],
                    "localizacoes",
                    type_="unique",
                    schema=DATABASE_SCHEMA,
                )

        for chave in inspector.get_foreign_keys(
                "localizacoes",
                schema=DATABASE_SCHEMA,
        ):
            if colunas_legadas & set(chave["constrained_columns"]):
                op.drop_constraint(
                    chave["name"],
                    "localizacoes",
                    type_="foreignkey",
                    schema=DATABASE_SCHEMA,
                )

        for indice in inspector.get_indexes(
                "localizacoes",
                schema=DATABASE_SCHEMA,
        ):
            if indice.get("duplicates_constraint"):
                continue
            if colunas_legadas & set(indice["column_names"]):
                op.drop_index(
                    indice["name"],
                    table_name="localizacoes",
                    schema=DATABASE_SCHEMA,
                )

        for coluna in sorted(colunas_legadas):
            op.drop_column("localizacoes", coluna, schema=DATABASE_SCHEMA)

    restricoes_unicas = sa.inspect(bind).get_unique_constraints(
        "localizacoes",
        schema=DATABASE_SCHEMA,
    )
    if not any(
            restricao["column_names"] == ["nome"]
            for restricao in restricoes_unicas
    ):
        op.create_unique_constraint(
            "uq_localizacoes_nome",
            "localizacoes",
            ["nome"],
            schema=DATABASE_SCHEMA,
        )


def upgrade() -> None:
    # A revisao 0002 atual ja produz a estrutura final em bancos novos. As
    # inspecoes abaixo existem para reparar bancos legados e exigem conexao real.
    if context.is_offline_mode():
        return

    vinculos = _carregar_vinculos()
    _preparar_schema_localizacoes()
    _criar_tabela_se_ausente()
    registros = _resolver_referencias(vinculos)
    _inserir_vinculos(registros)
    _validar_resultado(registros)
    _finalizar_schema_localizacoes()


def downgrade() -> None:
    # A tabela pode ter sido criada originalmente pela 0002. Preserva-se o dado
    # para que o downgrade da correcao nunca remova uma estrutura preexistente.
    return None

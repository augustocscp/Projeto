import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import func, inspect, select

from app.config import validate_database_schema
from app.models.categoria_patrimonial import CategoriaPatrimonial
from app.models.departamento import Departamento
from app.models.destinacao_patrimonial import DestinacaoPatrimonial
from app.models.estado_conservacao import EstadoConservacao
from app.models.filial import Filial
from app.models.localizacao import Localizacao, LocalizacaoVinculo
from app.models.situacao_patrimonial import SituacaoPatrimonial


def test_migrations_criam_estrutura_e_seeds(db):
    schema = os.environ["DATABASE_SCHEMA"]
    inspector = inspect(db.get_bind())
    tabelas = set(inspector.get_table_names(schema=schema))
    assert {
               "categorias_patrimoniais",
               "estados_conservacao",
               "situacoes_patrimoniais",
               "destinacoes_patrimoniais",
               "responsaveis",
               "patrimonios",
               "integracao_bigquery_staging",
               "patrimonios_contabeis",
               "historico_contabil",
               "historico_controle_patrimonial",
               "historico_sistema",
           } <= tabelas
    assert db.scalar(select(func.count(CategoriaPatrimonial.id))) == 7
    estados_ativos = db.scalars(
        select(EstadoConservacao)
        .where(EstadoConservacao.ativo.is_(True))
        .order_by(EstadoConservacao.ordem_exibicao)
    ).all()
    assert [estado.nome for estado in estados_ativos] == [
        "Ótimo",
        "Bom",
        "Regular",
        "Ruim",
        "Danificado",
        "Não avaliado",
    ]
    assert not db.scalars(
        select(EstadoConservacao).where(
            EstadoConservacao.nome.in_(("Novo", "Inservível"))
        )
    ).all()
    assert db.scalar(select(func.count(SituacaoPatrimonial.id))) == 7
    assert not db.scalars(
        select(SituacaoPatrimonial).where(
            SituacaoPatrimonial.nome.in_(("Ativo", "Em Transferência"))
        )
    ).all()
    destinacoes_ativas = db.scalars(
        select(DestinacaoPatrimonial)
        .where(DestinacaoPatrimonial.ativo.is_(True))
        .order_by(DestinacaoPatrimonial.ordem_exibicao)
    ).all()
    assert [destinacao.nome for destinacao in destinacoes_ativas] == [
        "Operacional",
        "Administrativo",
        "Almoxarifado",
        "Reserva Técnica",
        "Manutenção",
        "Treinamento",
        "Locado",
        "Comodato",
        "Descarte",
        "Venda",
        "Doação",
    ]

    colunas_por_tabela = {
        tabela: {
            coluna["name"]
            for coluna in inspect(db.get_bind()).get_columns(
                tabela, schema=os.environ["DATABASE_SCHEMA"]
            )
        }
        for tabela in (
            "categorias_patrimoniais",
            "cidades",
            "departamentos",
            "destinacoes_patrimoniais",
            "empresas",
            "estados_conservacao",
            "filiais",
        )
    }
    assert {"codigo", "descricao"}.isdisjoint(
        colunas_por_tabela["categorias_patrimoniais"]
    )
    assert "codigo_ibge" not in colunas_por_tabela["cidades"]
    assert "codigo" not in colunas_por_tabela["departamentos"]
    assert {"codigo", "descricao"}.isdisjoint(
        colunas_por_tabela["destinacoes_patrimoniais"]
    )
    assert "descricao" not in colunas_por_tabela["empresas"]
    assert "descricao" not in colunas_por_tabela["estados_conservacao"]
    assert "codigo" not in colunas_por_tabela["filiais"]

    assert db.scalar(select(func.count(Departamento.id))) == 17
    assert all(
        departamento.descricao
        for departamento in db.scalars(select(Departamento)).all()
    )

    total_vinculos = db.scalar(select(func.count(LocalizacaoVinculo.id)))
    vinculos_distintos = db.scalar(
        select(func.count()).select_from(
            select(
                LocalizacaoVinculo.localizacao_id,
                LocalizacaoVinculo.filial_id,
                LocalizacaoVinculo.departamento_id,
            )
            .distinct()
            .subquery()
        )
    )
    assert total_vinculos == 172
    assert vinculos_distintos == 172

    assert "patrimonio_numero_tombo_seq" in inspector.get_sequence_names(
        schema=schema
    )
    assert db.execute(
        sa.select(sa.literal_column("version_num")).select_from(
            sa.table(
                "alembic_version",
                sa.column("version_num", sa.String()),
                schema=schema,
            )
        )
    ).scalar_one() == "0019"

    namespaces = sa.table(
        "pg_namespace",
        sa.column("oid", sa.Integer()),
        sa.column("nspname", sa.String()),
        schema="pg_catalog",
    )
    classes = sa.table(
        "pg_class",
        sa.column("oid", sa.Integer()),
        sa.column("relnamespace", sa.Integer()),
        sa.column("relname", sa.String()),
        schema="pg_catalog",
    )
    procedures = sa.table(
        "pg_proc",
        sa.column("pronamespace", sa.Integer()),
        sa.column("proname", sa.String()),
        schema="pg_catalog",
    )
    triggers = sa.table(
        "pg_trigger",
        sa.column("tgrelid", sa.Integer()),
        sa.column("tgname", sa.String()),
        sa.column("tgisinternal", sa.Boolean()),
        schema="pg_catalog",
    )
    namespace_id = select(namespaces.c.oid).where(
        namespaces.c.nspname == schema
    ).scalar_subquery()
    assert db.scalar(
        select(func.count()).select_from(procedures).where(
            procedures.c.pronamespace == namespace_id,
            procedures.c.proname == "bloquear_mutacao_historico_sistema",
        )
    ) == 1
    assert db.scalar(
        select(func.count())
        .select_from(triggers.join(classes, classes.c.oid == triggers.c.tgrelid))
        .where(
            classes.c.relnamespace == namespace_id,
            classes.c.relname == "historico_sistema",
            triggers.c.tgname == "trg_historico_sistema_append_only",
            triggers.c.tgisinternal.is_(False),
        )
    ) == 1


@pytest.mark.parametrize(
    "schema",
    (
            "",
            "1gadm",
            "gadm.public",
            "gadm-test",
            "gadm test",
            'gadm"',
            "gadm;DROP_SCHEMA",
            "gadm--comentario",
            "a" * 64,
    ),
)
def test_database_schema_invalido_e_rejeitado(schema):
    with pytest.raises(RuntimeError):
        validate_database_schema(schema)


@pytest.mark.parametrize("schema", ("gadm", "_gadm", "a" * 63))
def test_database_schema_valido_e_aceito(schema):
    assert validate_database_schema(schema) == schema


def test_seeds_nao_possuem_codigos_duplicados(db):
    for model in (
            EstadoConservacao,
            SituacaoPatrimonial,
    ):
        total = db.scalar(select(func.count(model.id)))
        distintos = db.scalar(select(func.count(func.distinct(model.codigo))))
        assert total == distintos


def test_coordenacao_pertence_ao_escritorio_matriz(db):
    filiais = db.scalars(
        select(Filial)
        .join(LocalizacaoVinculo)
        .join(Localizacao)
        .where(Localizacao.nome.ilike("COORDENA%"))
        .distinct()
    ).all()

    assert filiais
    assert all(
        filial.tipo_unidade == "ESCRITORIO"
        and "matriz" in filial.nome.casefold()
        for filial in filiais
    )


def test_migrations_offline_usam_apenas_schema_configurado():
    schema = f"gadm_offline_{uuid4().hex}"
    backend_dir = Path(__file__).resolve().parents[1]
    ambiente = os.environ.copy()
    ambiente["DATABASE_SCHEMA"] = schema
    ambiente["PYTHONIOENCODING"] = "utf-8"
    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=backend_dir,
        env=ambiente,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr

    sql = resultado.stdout
    sql_normalizado = sql.lower().replace('"', "")
    create_schema = sql_normalizado.index(f"create schema if not exists {schema}")
    version_table = sql_normalizado.index(f"{schema}.alembic_version")
    assert create_schema < version_table
    assert "gadm." not in sql_normalizado
    assert "public." not in sql_normalizado
    assert not re.search(
        rf"create\s+(?:table|sequence)\s+(?!{re.escape(schema)}\.)",
        sql_normalizado,
    )

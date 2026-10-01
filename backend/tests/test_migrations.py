import os

import pytest
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
    tabelas = set(inspect(db.get_bind()).get_table_names(schema=os.environ["DATABASE_SCHEMA"]))
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

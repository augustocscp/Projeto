import os

from sqlalchemy import func, inspect, select

from app.models.categoria_patrimonial import CategoriaPatrimonial
from app.models.destinacao_patrimonial import DestinacaoPatrimonial
from app.models.estado_conservacao import EstadoConservacao
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
    assert db.scalar(select(func.count(EstadoConservacao.id))) == 6
    assert db.scalar(select(func.count(SituacaoPatrimonial.id))) == 9
    assert db.scalar(select(func.count(DestinacaoPatrimonial.id))) == 10


def test_seeds_nao_possuem_codigos_duplicados(db):
    for model in (
        EstadoConservacao,
        SituacaoPatrimonial,
        DestinacaoPatrimonial,
    ):
        total = db.scalar(select(func.count(model.id)))
        distintos = db.scalar(select(func.count(func.distinct(model.codigo))))
        assert total == distintos

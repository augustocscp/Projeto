from sqlalchemy import func, select

from app.models.integracao_bigquery_staging import IntegracaoBigQueryStaging
from app.services import integracao_bigquery_service


class FakeProtheusService:
    def consultar_codigo(self, codigo):
        return {
            "SN1": [{"campo_desconhecido": "valor", "codigo_recebido": codigo}],
            "SN3": [],
            "SNG": [{"outro_campo": 10}],
        }


def test_integracao_desativada_nao_retorna_erro(client):
    response = client.get("/api/integracoes/protheus-bigquery/123456")
    assert response.status_code == 200
    assert response.json()["integracao_ativa"] is False


def test_mock_persiste_retorno_bruto_sem_transformacao(db, contexto, monkeypatch):
    monkeypatch.setattr(integracao_bigquery_service, "GCP_BIGQUERY_ENABLED", True)
    resultado = integracao_bigquery_service.consultar_e_armazenar(
        db,
        "123456",
        contexto["usuario"].id,
        FakeProtheusService(),
    )
    assert resultado["integracao_ativa"] is True
    assert resultado["registros_encontrados"]["SN1"][0]["campo_desconhecido"] == "valor"
    assert db.scalar(select(func.count(IntegracaoBigQueryStaging.id))) == 2
    staging = db.scalar(
        select(IntegracaoBigQueryStaging).where(
            IntegracaoBigQueryStaging.tabela_origem == "SN1"
        )
    )
    assert staging.dados_json == {
        "campo_desconhecido": "valor",
        "codigo_recebido": "123456",
    }
    assert len(staging.hash_registro) == 64


def test_cadastro_independe_da_integracao(client, contexto):
    response = client.post("/api/patrimonios", json=contexto["payload"])
    assert response.status_code == 201

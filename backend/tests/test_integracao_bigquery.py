from app.integrations.protheus_contabil_service import ProtheusContabilService
from app.integrations.protheus_responsavel_service import ProtheusResponsavelService
from app.integrations.normalizacao import (
    normalizar_codigo_protheus,
    normalizar_codigo_re,
    normalizar_numero_item,
    normalizar_numero_plaqueta,
)
from fastapi.testclient import TestClient
from app.auth import get_current_user
from app.main import app


class FakeClient:
    def __init__(self):
        self.chamadas = []

    def consultar_tabela(self, tabela, filtros):
        self.chamadas.append((tabela, filtros))
        if "SN1" in tabela:
            return [
                {
                    "N1_VLAQUIS": "100",
                    "N1_BAIXA": "",
                    "N1_FORNEC": "FORNECEDOR-01",
                    "N1_LOJA": "0001",
                }
            ]
        if "SN3" in tabela:
            return [{"N3_TIPO": "10", "N3_VRDACM1": "20"}]
        if "funcionarios" in tabela:
            return [{"NOMEFUNCIONARIO": "Pessoa", "CARGO": "Cargo", "DESCRICAO_SETOR": "Setor"}]
        return [{"CTT_XEQUIP": "Departamento externo", "CTT_XRESPO": "  NOME DO GESTOR  "}]


def test_contabil_sempre_filtra_tipo_10(monkeypatch):
    monkeypatch.setattr("app.integrations.protheus_contabil_service.BIGQUERY_TABLE_SN1", "x.SN1")
    monkeypatch.setattr("app.integrations.protheus_contabil_service.BIGQUERY_TABLE_SN3", "x.SN3")
    client = FakeClient()
    resultado = ProtheusContabilService(client).consultar("1", "2")
    assert resultado["valor_atual"] == 80
    assert resultado["fornecedor"] == "FORNECEDOR-01"
    assert client.chamadas[1][1] == {"N3_CBASE": "0000000001", "N3_ITEM": "0002", "N3_TIPO": "10"}


def test_codigo_protheus_completa_zeros_a_esquerda():
    assert normalizar_codigo_protheus("6003") == "0000006003"
    assert normalizar_codigo_protheus("sp30001071") == "SP30001071"
    assert normalizar_numero_item("2") == "0002"
    assert normalizar_numero_plaqueta("123") == "0000000123"
    assert normalizar_codigo_re("123") == "00123"


def test_responsavel_sempre_filtra_current_e_ativo(monkeypatch):
    monkeypatch.setattr("app.integrations.protheus_responsavel_service.BIGQUERY_TABLE_FUNCIONARIOS", "x.funcionarios")
    monkeypatch.setattr("app.integrations.protheus_responsavel_service.BIGQUERY_TABLE_CTT", "x.CTT")
    client = FakeClient()
    resultado = ProtheusResponsavelService(client).consultar("123")
    assert resultado["gestor_responsavel"] == "  NOME DO GESTOR  "
    assert client.chamadas[0][1] == {"MATRICULA": "00123", "IS_CURRENT": True, "CODSITUACAO": "A"}


def test_responsavel_inativo_usa_consulta_diagnostica(monkeypatch):
    monkeypatch.setattr("app.integrations.protheus_responsavel_service.BIGQUERY_TABLE_FUNCIONARIOS", "x.funcionarios")
    monkeypatch.setattr("app.integrations.protheus_responsavel_service.BIGQUERY_TABLE_CTT", "x.CTT")

    class InativoClient:
        def __init__(self): self.chamadas = []

        def consultar_tabela(self, tabela, filtros):
            self.chamadas.append(filtros)
            return [] if "CODSITUACAO" in filtros else [{"CODSITUACAO": "D"}, {"CODSITUACAO": "D"}]

    client = InativoClient()
    resultado = ProtheusResponsavelService(client).consultar("123")
    assert resultado == {"status": "inativo", "multiplos_current": True}
    assert client.chamadas[1] == {"MATRICULA": "00123", "IS_CURRENT": True}


def test_endpoints_exploratorios_integracao_desativada():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "teste@example.com"}
    with TestClient(app) as client:
        respostas = (
            client.get("/api/patrimonios/protheus-cadastral?codigo_protheus=1&numero_item=2"),
            client.get("/api/patrimonios/protheus-contabil?codigo_protheus=1&numero_item=2"),
            client.get("/api/responsaveis/protheus?codigo_re=123"),
        )
    app.dependency_overrides.clear()
    assert all(response.status_code == 200 for response in respostas)
    assert all(response.json()["integracao_ativa"] is False for response in respostas)

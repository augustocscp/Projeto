from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models.departamento import Departamento
from app.models.filial import Filial
from app.models.localizacao import LocalizacaoVinculo
from app.models.situacao_patrimonial import SituacaoPatrimonial
from app.models.historico_controle_patrimonial import HistoricoControlePatrimonial
from app.models.historico_contabil import HistoricoContabil
from app.models.historico_sistema import HistoricoSistema
from app.models.patrimonio import Patrimonio
from app.services.contabilidade_service import atualizar_snapshot
from app.schemas.patrimonio import PatrimonioCreate
from app.services.patrimonio_service import _proximo_numero_tombo
from app.services.responsavel_service import resolver_responsavel


def test_criacao_manual_valida(client, contexto):
    payload = contexto["payload"] | {
        "codigo_protheus": "6003",
        "numero_item": "2",
        "numero_plaqueta_fisica": "123",
        "codigo_re": "123",
        "numero_serie": None,
    }
    response = client.post("/api/patrimonios", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(r"PAT-\d{6,}", body["numero_tombo"])
    assert body["numero_item"] == "0002"
    assert body["numero_plaqueta_fisica"] == "0000000123"
    assert body["codigo_protheus"] == "0000006003"
    assert body["numero_serie"] is None
    assert body["protheus_status"] is None


def test_cria_responsavel_consultado_no_protheus(db, monkeypatch):
    class ProtheusFake:
        def consultar(self, codigo_re):
            assert codigo_re == "05360"
            return {
                "status": "ativo",
                "nome": "Responsável Protheus",
                "cargo": "Coordenador",
                "departamento_externo": "Administrativo",
                "gestor_responsavel": "Gestor Externo",
                "ctt_encontrado": True,
                "multiplos_current": False,
            }

    monkeypatch.setattr(
        "app.services.responsavel_service.GCP_BIGQUERY_ENABLED",
        True,
    )

    responsavel = resolver_responsavel(
        db,
        "05360",
        service=ProtheusFake(),
    )

    assert responsavel.codigo_re == "05360"
    assert responsavel.gestor_responsavel == "Gestor Externo"
    assert responsavel.gestor is None


def test_filtros_de_localizacao_seguem_empresa_departamento_filial(
    client,
    contexto,
):
    empresa_id = contexto["payload"]["empresa_id"]
    departamentos = client.get(
        f"/api/departamentos?empresa_id={empresa_id}"
    ).json()
    departamento_dp = next(
        item for item in departamentos if item["codigo"] == "DP"
    )

    response = client.get(
        "/api/filiais",
        params={
            "empresa_id": empresa_id,
            "departamento_id": departamento_dp["id"],
        },
    )

    assert response.status_code == 200
    filiais = response.json()
    assert len(filiais) == 1
    assert "matriz" in filiais[0]["nome"].casefold()


def test_categoria_inexistente(client, contexto):
    payload = contexto["payload"] | {"categoria_id": 999999}
    response = client.post("/api/patrimonios", json=payload)
    assert response.status_code == 404


def test_localizacao_invalida(client, contexto, db):
    outro_departamento = db.scalar(
        select(Departamento.id).where(
            Departamento.id != contexto["payload"]["departamento_id"]
        )
    )
    payload = contexto["payload"] | {"departamento_id": outro_departamento}
    response = client.post("/api/patrimonios", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["codigo"] == "LOCALIZACAO_INVALIDA"


def test_categoria_inativa_nao_pode_ser_usada(client, contexto, db):
    contexto["categoria"].ativo = False
    db.commit()
    response = client.post("/api/patrimonios", json=contexto["payload"])
    assert response.status_code == 422
    assert response.json()["detail"]["codigo"] == "CATEGORIA_INATIVO"


def test_responsavel_inexistente(client, contexto):
    payload = contexto["payload"] | {"codigo_re": "99999"}
    response = client.post("/api/patrimonios", json=payload)
    assert response.status_code == 503


def test_garantia_true_exige_data(client, contexto):
    response = client.post(
        "/api/patrimonios",
        json=contexto["payload"] | {"possui_garantia": True},
    )
    assert response.status_code == 422


def test_garantia_false_rejeita_data(client, contexto):
    response = client.post(
        "/api/patrimonios",
        json=contexto["payload"] | {"data_fim_garantia": date.today().isoformat()},
    )
    assert response.status_code == 422


def test_plaqueta_duplicada(client, contexto):
    assert client.post("/api/patrimonios", json=contexto["payload"]).status_code == 201
    response = client.post("/api/patrimonios", json=contexto["payload"])
    assert response.status_code == 409


def test_consulta_inexistente(client):
    response = client.get("/api/patrimonios/999999")
    assert response.status_code == 404


def test_atualizacao_inativacao_e_resumo(client, contexto, db):
    created = client.post("/api/patrimonios", json=contexto["payload"]).json()
    updated = client.patch(
        f"/api/patrimonios/{created['id']}", json={"descricao": "Atualizado"}
    )
    assert updated.status_code == 200
    assert updated.json()["descricao"] == "Atualizado"
    historicos = list(db.scalars(select(HistoricoControlePatrimonial)))
    assert any(item.campo_alterado == "descricao" for item in historicos)
    inactivated = client.patch(f"/api/patrimonios/{created['id']}/inativar")
    assert inactivated.status_code == 200
    assert inactivated.json()["ativo"] is False
    resumo = client.get("/api/patrimonio/resumo").json()["indicadores"]
    assert resumo["bensCadastrados"] == 1
    assert resumo["bensInativos"] == 1


def test_rejeita_todos_em_localizacao(client, contexto):
    response = client.post("/api/patrimonios", json=contexto["payload"] | {"empresa_id": "Todos"})
    assert response.status_code == 422


def test_snapshot_historico_e_divergencia_baixa(client, contexto, db, monkeypatch):
    criado = client.post("/api/patrimonios", json=contexto["payload"]).json()
    patrimonio = db.get(Patrimonio, criado["id"])
    monkeypatch.setattr("app.services.contabilidade_service.GCP_BIGQUERY_ENABLED", True)

    class FakeContabil:
        def __init__(self, valor): self.valor = valor

        def consultar(self, codigo, item):
            return {
                "numero_nota_fiscal": "NF", "serie_nota_fiscal": "1", "data_nota_fiscal": None,
                "codigo_fornecedor": None, "fornecedor": None, "valor_aquisicao": self.valor,
                "icms": None, "valor_atual": self.valor, "percentual_depreciacao": None,
                "depreciacao_mensal": None, "depreciacao_acumulada": None,
                "inicio_depreciacao": None, "fim_depreciacao": None, "conta_contabil": None,
                "centro_custo": None, "data_baixa_sn1": datetime.now(timezone.utc), "data_baixa_sn3": None,
                "consultado_em": patrimonio.data_cadastro, "dados_brutos_sn1": {}, "dados_brutos_sn3": {},
                "multiplos_sn3": False, "divergencia_baixa": True,
            }

    atualizar_snapshot(db, patrimonio, contexto["usuario"].id, FakeContabil(100))
    assert db.scalar(select(HistoricoContabil.id)) is None
    assert db.scalar(select(HistoricoSistema).where(HistoricoSistema.tipo_evento == "DIVERGENCIA_BAIXA")) is not None
    db.expire(patrimonio, ["contabil"])
    atualizar_snapshot(db, patrimonio, contexto["usuario"].id, FakeContabil(90))
    assert db.scalar(select(HistoricoContabil).where(HistoricoContabil.campo_alterado == "valor_aquisicao")) is not None


def test_patrimonio_baixado_nao_pode_ser_movimentado(client, contexto, db):
    baixado_id = db.scalar(
        select(SituacaoPatrimonial.id).where(SituacaoPatrimonial.codigo == "BAIXADO")
    )
    payload = contexto["payload"] | {
        "situacao_id": baixado_id,
    }
    created = client.post("/api/patrimonios", json=payload).json()
    outro_vinculo = db.scalar(
        select(LocalizacaoVinculo).where(
            LocalizacaoVinculo.localizacao_id != payload["localizacao_id"]
        )
    )
    outra_filial = db.get(Filial, outro_vinculo.filial_id)
    response = client.patch(
        f"/api/patrimonios/{created['id']}",
        json={
            "empresa_id": outra_filial.empresa_id,
            "filial_id": outro_vinculo.filial_id,
            "departamento_id": outro_vinculo.departamento_id,
            "localizacao_id": outro_vinculo.localizacao_id,
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["codigo"] == "PATRIMONIO_BAIXADO_NAO_MOVIMENTAVEL"


def test_numero_tombo_concorrente(migrated_database):
    def gerar(_):
        with Session(engine) as session:
            return _proximo_numero_tombo(session)

    with ThreadPoolExecutor(max_workers=8) as executor:
        tombos = list(executor.map(gerar, range(16)))
    assert len(tombos) == len(set(tombos)) == 16


def test_schema_create_nao_aceita_campos_controlados(contexto):
    payload = contexto["payload"] | {"numero_tombo": "INVÁLIDO"}
    try:
        PatrimonioCreate.model_validate(payload)
    except Exception as exc:
        assert "numero_tombo" in str(exc)
    else:
        raise AssertionError("Campo controlado foi aceito")

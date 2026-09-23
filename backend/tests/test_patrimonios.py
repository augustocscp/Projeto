from concurrent.futures import ThreadPoolExecutor
from datetime import date
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models.departamento import Departamento
from app.models.filial import Filial
from app.models.localizacao import LocalizacaoVinculo
from app.models.situacao_patrimonial import SituacaoPatrimonial
from app.schemas.patrimonio import PatrimonioCreate
from app.services.patrimonio_service import _proximo_numero_tombo


def test_criacao_manual_valida(client, contexto):
    response = client.post("/api/patrimonios", json=contexto["payload"])
    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(r"PAT-\d{6,}", body["numero_tombo"])
    assert body["numero_plaqueta_fisica"] == "PLAQ-TESTE-001"
    assert body["protheus_status"] is None


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
    payload = contexto["payload"] | {"responsavel_id": 999999}
    response = client.post("/api/patrimonios", json=payload)
    assert response.status_code == 404


def test_baixado_exige_data(client, contexto, db):
    baixado_id = db.scalar(
        select(SituacaoPatrimonial.id).where(SituacaoPatrimonial.codigo == "BAIXADO")
    )
    response = client.post(
        "/api/patrimonios",
        json=contexto["payload"] | {"situacao_id": baixado_id},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["codigo"] == "DATA_BAIXA_OBRIGATORIA"


def test_situacao_ativa_rejeita_data_baixa(client, contexto):
    response = client.post(
        "/api/patrimonios",
        json=contexto["payload"] | {"data_baixa": date.today().isoformat()},
    )
    assert response.status_code == 422


def test_plaqueta_duplicada(client, contexto):
    assert client.post("/api/patrimonios", json=contexto["payload"]).status_code == 201
    response = client.post("/api/patrimonios", json=contexto["payload"])
    assert response.status_code == 409


def test_consulta_inexistente(client):
    response = client.get("/api/patrimonios/999999")
    assert response.status_code == 404


def test_atualizacao_inativacao_e_resumo(client, contexto):
    created = client.post("/api/patrimonios", json=contexto["payload"]).json()
    updated = client.patch(
        f"/api/patrimonios/{created['id']}", json={"descricao": "Atualizado"}
    )
    assert updated.status_code == 200
    assert updated.json()["descricao"] == "Atualizado"
    inactivated = client.patch(f"/api/patrimonios/{created['id']}/inativar")
    assert inactivated.status_code == 200
    assert inactivated.json()["ativo"] is False
    resumo = client.get("/api/patrimonio/resumo").json()["indicadores"]
    assert resumo["bensCadastrados"] == 1
    assert resumo["bensInativos"] == 1


def test_patrimonio_baixado_nao_pode_ser_movimentado(client, contexto, db):
    baixado_id = db.scalar(
        select(SituacaoPatrimonial.id).where(SituacaoPatrimonial.codigo == "BAIXADO")
    )
    payload = contexto["payload"] | {
        "situacao_id": baixado_id,
        "data_baixa": date.today().isoformat(),
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
    assert response.json()["detail"]["codigo"] == "PATRIMONIO_BAIXADO"


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

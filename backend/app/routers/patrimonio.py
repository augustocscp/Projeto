from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.config import GCP_BIGQUERY_ENABLED
from app.errors import api_error
from app.integrations.bigquery_client import BigQueryIntegrationError
from app.integrations.protheus_contabil_service import ProtheusContabilService
from app.integrations.protheus_patrimonio_service import ProtheusPatrimonioService
from app.schemas.patrimonio import (
    PatrimonioCreate,
    PatrimonioListResponse,
    PatrimonioResponse,
    PatrimonioUpdate,
)
from app.services.patrimonio_service import (
    atualizar_patrimonio,
    criar_patrimonio,
    inativar_patrimonio,
    listar_patrimonios,
    obter_patrimonio,
    patrimonio_response,
    resumo_patrimonial,
    contabil_response,
)
from app.services.contabilidade_service import atualizar_snapshot
from app.services.historico_service import historico_agregado, registrar_evento

router = APIRouter(tags=["patrimonios"])


@router.get("/api/patrimonios/protheus-cadastral")
def consultar_protheus_cadastral(codigo_protheus: str, numero_item: str, user=Depends(get_current_user),
                                 db: Session = Depends(get_db)):
    if not GCP_BIGQUERY_ENABLED:
        return {"integracao_ativa": False, "encontrado": False, "dados": None}
    try:
        dados = ProtheusPatrimonioService().consultar(codigo_protheus, numero_item)
    except BigQueryIntegrationError as exc:
        registrar_evento(db, "FALHA_INTEGRACAO", "Falha na consulta cadastral exploratória.", usuario_id=user["id"]);
        db.commit()
        raise api_error(503, "INTEGRACAO_INDISPONIVEL", "Integração com o Protheus indisponível.") from exc
    if dados is None:
        raise api_error(404, "PATRIMONIO_PROTHEUS_NAO_ENCONTRADO", "Bem não encontrado no Protheus.")
    return {"integracao_ativa": True, "encontrado": True, "dados": dados}


@router.get("/api/patrimonios/protheus-contabil")
def consultar_protheus_contabil(codigo_protheus: str, numero_item: str, user=Depends(get_current_user),
                                db: Session = Depends(get_db)):
    if not GCP_BIGQUERY_ENABLED:
        return {"integracao_ativa": False, "encontrado": False, "dados": None}
    try:
        dados = ProtheusContabilService().consultar(codigo_protheus, numero_item)
    except BigQueryIntegrationError as exc:
        registrar_evento(db, "FALHA_INTEGRACAO", "Falha na consulta contábil exploratória.", usuario_id=user["id"]);
        db.commit()
        raise api_error(503, "INTEGRACAO_INDISPONIVEL", "Integração com o Protheus indisponível.") from exc
    if dados is None:
        raise api_error(404, "PATRIMONIO_PROTHEUS_NAO_ENCONTRADO", "Bem não encontrado no Protheus.")
    return {"integracao_ativa": True, "encontrado": True, "dados": dados}


@router.get("/api/patrimonios", response_model=PatrimonioListResponse)
def listar(
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
        pagina: Annotated[int, Query(ge=1)] = 1,
        tamanho: Annotated[int, Query(ge=1, le=100)] = 20,
        numero_tombo: str | None = None,
        codigo_protheus: str | None = None,
        numero_plaqueta_fisica: str | None = None,
        situacao_id: int | None = None,
        categoria_id: int | None = None,
        filial_id: int | None = None,
        departamento_id: int | None = None,
        localizacao_id: int | None = None,
        responsavel_id: int | None = None,
        ativo: bool | None = None,
):
    resultado = listar_patrimonios(
        db,
        pagina,
        tamanho,
        {
            "numero_tombo": numero_tombo,
            "codigo_protheus": codigo_protheus,
            "numero_plaqueta_fisica": numero_plaqueta_fisica,
            "situacao_id": situacao_id,
            "categoria_id": categoria_id,
            "filial_id": filial_id,
            "departamento_id": departamento_id,
            "localizacao_id": localizacao_id,
            "responsavel_id": responsavel_id,
            "ativo": ativo,
        },
    )
    resultado["items"] = [patrimonio_response(item) for item in resultado["items"]]
    return resultado


@router.get("/api/patrimonios/{patrimonio_id}", response_model=PatrimonioResponse)
def consultar(
        patrimonio_id: int,
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    patrimonio = obter_patrimonio(db, patrimonio_id)
    _, cache = atualizar_snapshot(db, patrimonio, user["id"])
    patrimonio = obter_patrimonio(db, patrimonio_id)
    resposta = patrimonio_response(patrimonio)
    resposta["contabil"] = contabil_response(patrimonio.contabil)
    resposta["contabil_em_cache"] = cache
    return resposta


@router.get("/api/patrimonios/{patrimonio_id}/historico")
def historico(patrimonio_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    obter_patrimonio(db, patrimonio_id)
    return historico_agregado(db, patrimonio_id)


@router.post(
    "/api/patrimonios",
    response_model=PatrimonioResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
        payload: PatrimonioCreate,
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    return patrimonio_response(criar_patrimonio(db, payload, user["id"]))


@router.patch("/api/patrimonios/{patrimonio_id}", response_model=PatrimonioResponse)
def atualizar(
        patrimonio_id: int,
        payload: PatrimonioUpdate,
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    return patrimonio_response(
        atualizar_patrimonio(db, patrimonio_id, payload, user["id"])
    )


@router.patch(
    "/api/patrimonios/{patrimonio_id}/inativar",
    response_model=PatrimonioResponse,
)
def inativar(
        patrimonio_id: int,
        user=Depends(get_current_user),
        db: Session = Depends(get_db),
):
    return patrimonio_response(inativar_patrimonio(db, patrimonio_id, user["id"]))


@router.get("/api/patrimonio/resumo")
def resumo(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "usuario": user["email"],
        "indicadores": resumo_patrimonial(db),
    }

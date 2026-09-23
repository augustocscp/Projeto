from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
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
)

router = APIRouter(tags=["patrimonios"])


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
    return patrimonio_response(obter_patrimonio(db, patrimonio_id))


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

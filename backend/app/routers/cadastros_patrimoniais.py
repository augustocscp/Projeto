from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.config import GCP_BIGQUERY_ENABLED
from app.errors import api_error
from app.integrations.bigquery_client import BigQueryIntegrationError
from app.integrations.protheus_responsavel_service import ProtheusResponsavelService
from app.models.categoria_patrimonial import CategoriaPatrimonial
from app.models.departamento import Departamento
from app.models.destinacao_patrimonial import DestinacaoPatrimonial
from app.models.empresa import Empresa
from app.models.estado_conservacao import EstadoConservacao
from app.models.filial import Filial
from app.models.localizacao import LocalizacaoVinculo
from app.models.situacao_patrimonial import SituacaoPatrimonial
from app.schemas.categoria_patrimonial import CategoriaPatrimonialResponse
from app.schemas.destinacao_patrimonial import DestinacaoPatrimonialResponse
from app.schemas.estado_conservacao import EstadoConservacaoResponse
from app.schemas.responsavel import ResponsavelResponse
from app.schemas.situacao_patrimonial import SituacaoPatrimonialResponse
from app.services.localizacao_service import listar_localizacoes
from app.services.responsavel_service import listar_responsaveis
from app.services.historico_service import registrar_evento

router = APIRouter(
    tags=["cadastros-patrimoniais"], dependencies=[Depends(get_current_user)]
)


@router.get("/api/responsaveis/protheus")
def responsavel_protheus(
    codigo_re: Annotated[
        str,
        Query(min_length=1, max_length=5, pattern=r"^[A-Za-z0-9]+$"),
    ],
    db: Session = Depends(get_db),
):
    if not GCP_BIGQUERY_ENABLED:
        return {"integracao_ativa": False, "encontrado": False, "dados": None}
    try:
        dados = ProtheusResponsavelService().consultar(codigo_re)
    except BigQueryIntegrationError as exc:
        registrar_evento(db, "FALHA_INTEGRACAO", "Falha na consulta exploratória de responsável.",
                         contexto={"codigo_re": codigo_re});
        db.commit()
        raise api_error(503, "INTEGRACAO_INDISPONIVEL", "Integração com o Protheus indisponível.") from exc
    if dados.get("multiplos_current"):
        registrar_evento(db, "FALHA_INTEGRACAO", "Mais de um registro current encontrado para o RE.",
                         contexto={"codigo_re": codigo_re});
        db.commit()
    if dados["status"] == "inativo":
        raise api_error(409, "RESPONSAVEL_INATIVO", "O RE informado não está ativo no sistema.")
    if dados["status"] == "nao_encontrado":
        raise api_error(404, "RESPONSAVEL_NAO_ENCONTRADO", "Responsável não encontrado no Protheus.")
    return {"integracao_ativa": True, "encontrado": True, "dados": dados}


def _referencia(registro, codigo_attr: str = "codigo") -> dict:
    return {
        "id": registro.id,
        "codigo": getattr(registro, codigo_attr, None),
        "nome": registro.nome,
        "ativo": registro.ativo,
    }


@router.get(
    "/api/categorias-patrimoniais",
    response_model=list[CategoriaPatrimonialResponse],
)
def categorias(ativo: bool | None = True, db: Session = Depends(get_db)):
    stmt = select(CategoriaPatrimonial).order_by(CategoriaPatrimonial.nome)
    if ativo is not None:
        stmt = stmt.where(CategoriaPatrimonial.ativo.is_(ativo))
    return list(db.scalars(stmt).all())


@router.get(
    "/api/estados-conservacao", response_model=list[EstadoConservacaoResponse]
)
def estados(ativo: bool | None = True, db: Session = Depends(get_db)):
    stmt = select(EstadoConservacao).order_by(EstadoConservacao.ordem_exibicao)
    if ativo is not None:
        stmt = stmt.where(EstadoConservacao.ativo.is_(ativo))
    return list(db.scalars(stmt).all())


@router.get(
    "/api/situacoes-patrimoniais", response_model=list[SituacaoPatrimonialResponse]
)
def situacoes(ativo: bool | None = True, db: Session = Depends(get_db)):
    stmt = select(SituacaoPatrimonial).order_by(SituacaoPatrimonial.ordem_exibicao)
    if ativo is not None:
        stmt = stmt.where(SituacaoPatrimonial.ativo.is_(ativo))
    return list(db.scalars(stmt).all())


@router.get(
    "/api/destinacoes-patrimoniais",
    response_model=list[DestinacaoPatrimonialResponse],
)
def destinacoes(ativo: bool | None = True, db: Session = Depends(get_db)):
    stmt = select(DestinacaoPatrimonial).order_by(
        DestinacaoPatrimonial.ordem_exibicao
    )
    if ativo is not None:
        stmt = stmt.where(DestinacaoPatrimonial.ativo.is_(ativo))
    return list(db.scalars(stmt).all())


@router.get("/api/empresas")
def empresas(ativo: bool | None = True, db: Session = Depends(get_db)):
    stmt = select(Empresa).order_by(Empresa.nome)
    if ativo is not None:
        stmt = stmt.where(Empresa.ativo.is_(ativo))
    return [_referencia(item) for item in db.scalars(stmt).all()]


@router.get("/api/filiais")
def filiais(
        empresa_id: int | None = None,
        departamento_id: int | None = None,
        ativo: bool | None = True,
        db: Session = Depends(get_db),
):
    stmt = select(Filial).order_by(Filial.nome)
    if empresa_id is not None:
        stmt = stmt.where(Filial.empresa_id == empresa_id)
    if departamento_id is not None:
        stmt = (
            stmt.join(LocalizacaoVinculo)
            .where(
                LocalizacaoVinculo.departamento_id == departamento_id,
                LocalizacaoVinculo.ativo.is_(True),
            )
            .distinct()
        )
    if ativo is not None:
        stmt = stmt.where(Filial.ativo.is_(ativo))
    return [
        _referencia(item)
        | {
            "tipo_unidade": item.tipo_unidade,
            "cidade": {
                "id": item.cidade.id,
                "nome": item.cidade.nome,
                "uf": item.cidade.uf,
            },
        }
        for item in db.scalars(stmt).all()
    ]


@router.get("/api/departamentos")
def departamentos(
        empresa_id: int | None = None,
        ativo: bool | None = True,
        db: Session = Depends(get_db),
):
    stmt = select(Departamento).order_by(Departamento.nome)
    if empresa_id is not None:
        stmt = (
            stmt.join(LocalizacaoVinculo)
            .join(Filial, Filial.id == LocalizacaoVinculo.filial_id)
            .where(
                Filial.empresa_id == empresa_id,
                Filial.ativo.is_(True),
                LocalizacaoVinculo.ativo.is_(True),
            )
            .distinct()
        )
    if ativo is not None:
        stmt = stmt.where(Departamento.ativo.is_(ativo))
    return [_referencia(item) for item in db.scalars(stmt).all()]


@router.get("/api/responsaveis", response_model=list[ResponsavelResponse])
def responsaveis(ativo: bool | None = True, db: Session = Depends(get_db)):
    return listar_responsaveis(db, ativo)


@router.get("/api/localizacoes")
def localizacoes(
        filial_id: int,
        departamento_id: int,
        db: Session = Depends(get_db),
):
    return [
        _referencia(item)
        for item in listar_localizacoes(db, filial_id, departamento_id)
    ]

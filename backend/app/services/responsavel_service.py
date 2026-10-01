from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models.responsavel import Responsavel
from app.config import GCP_BIGQUERY_ENABLED
from app.integrations.protheus_responsavel_service import ProtheusResponsavelService
from app.integrations.bigquery_client import BigQueryIntegrationError
from app.integrations.normalizacao import normalizar_codigo_re
from app.services.historico_service import registrar_evento


def listar_responsaveis(db: Session, ativo: bool | None = True) -> list[Responsavel]:
    stmt = select(Responsavel).order_by(Responsavel.nome)
    if ativo is not None:
        stmt = stmt.where(Responsavel.ativo.is_(ativo))
    return list(db.scalars(stmt).all())


def validar_responsavel(db: Session, responsavel_id: int) -> Responsavel:
    responsavel = db.get(Responsavel, responsavel_id)
    if responsavel is None:
        raise api_error(
            404,
            "RESPONSAVEL_NAO_ENCONTRADO",
            "Responsável não encontrado.",
            ["responsavel_id"],
        )
    if not responsavel.ativo:
        raise api_error(
            422,
            "RESPONSAVEL_INATIVO",
            "O responsável informado está inativo.",
            ["responsavel_id"],
        )
    return responsavel


def resolver_responsavel(db: Session, codigo_re: str, usuario_id: int | None = None,
                         patrimonio_id: int | None = None,
                         service: ProtheusResponsavelService | None = None) -> Responsavel:
    codigo_re = normalizar_codigo_re(codigo_re)
    responsavel = db.scalar(select(Responsavel).where(Responsavel.codigo_re == codigo_re))
    if responsavel is not None:
        if not responsavel.ativo:
            raise api_error(409, "RESPONSAVEL_INATIVO", "O RE informado não está ativo no sistema.", ["codigo_re"])
        return responsavel
    if not GCP_BIGQUERY_ENABLED:
        raise api_error(503, "INTEGRACAO_INDISPONIVEL",
                        "Não foi possível validar o RE informado. A integração com o Protheus está desativada e este responsável ainda não está cadastrado no sistema.",
                        ["codigo_re"])

    try:
        resultado = (service or ProtheusResponsavelService()).consultar(codigo_re)
    except BigQueryIntegrationError as exc:
        registrar_evento(db, "FALHA_INTEGRACAO", "Falha técnica ao validar responsável no Protheus.",
                         patrimonio_id=patrimonio_id, usuario_id=usuario_id, contexto={"codigo_re": codigo_re})
        db.commit()
        raise api_error(503, "INTEGRACAO_INDISPONIVEL", "Não foi possível validar o RE informado.",
                        ["codigo_re"]) from exc
    if resultado.get("multiplos_current"):
        registrar_evento(db, "FALHA_INTEGRACAO", "Mais de um registro current encontrado para o RE.",
                         patrimonio_id=patrimonio_id, usuario_id=usuario_id, contexto={"codigo_re": codigo_re})
    if resultado["status"] == "inativo":
        raise api_error(409, "RESPONSAVEL_INATIVO", "O RE informado não está ativo no sistema.", ["codigo_re"])
    if resultado["status"] == "nao_encontrado":
        raise api_error(404, "RESPONSAVEL_NAO_ENCONTRADO", "Responsável não encontrado no Protheus.", ["codigo_re"])
    if not resultado["ctt_encontrado"]:
        registrar_evento(db, "FALHA_INTEGRACAO", "Setor do responsável não encontrado na CTT.",
                         patrimonio_id=patrimonio_id, usuario_id=usuario_id, contexto={"codigo_re": codigo_re})
    responsavel = Responsavel(
        codigo_re=codigo_re, nome=resultado["nome"] or codigo_re, cargo=resultado["cargo"],
        departamento_id=None, departamento_externo=resultado["departamento_externo"],
        gestor_responsavel=resultado["gestor_responsavel"], origem_dados="API", ativo=True,
        consultado_em=datetime.now(timezone.utc),
    )
    db.add(responsavel)
    db.flush()
    return responsavel

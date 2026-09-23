from datetime import datetime, timezone
from hashlib import sha256
import json

from sqlalchemy.orm import Session

from app.config import GCP_BIGQUERY_ENABLED
from app.integrations.protheus_bigquery_service import ProtheusBigQueryService
from app.models.integracao_bigquery_staging import IntegracaoBigQueryStaging


def consultar_e_armazenar(
    db: Session,
    codigo_protheus: str,
    usuario_id: int,
    protheus_service: ProtheusBigQueryService | None = None,
) -> dict:
    consultado_em = datetime.now(timezone.utc)
    if not GCP_BIGQUERY_ENABLED:
        return {
            "codigo_protheus": codigo_protheus,
            "integracao_ativa": False,
            "registros_encontrados": {"SN1": [], "SN3": [], "SNG": []},
            "consultado_em": consultado_em,
            "mensagem": "Integração BigQuery desativada por configuração.",
        }

    registros = (protheus_service or ProtheusBigQueryService()).consultar_codigo(
        codigo_protheus
    )
    for tabela_origem, itens in registros.items():
        for item in itens:
            serializado = json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            db.add(
                IntegracaoBigQueryStaging(
                    tabela_origem=tabela_origem,
                    codigo_protheus_consultado=codigo_protheus,
                    dados_json=json.loads(serializado),
                    hash_registro=sha256(serializado.encode("utf-8")).hexdigest(),
                    consultado_em=consultado_em,
                    usuario_id=usuario_id,
                    processado=False,
                )
            )
    db.commit()
    return {
        "codigo_protheus": codigo_protheus,
        "integracao_ativa": True,
        "registros_encontrados": registros,
        "consultado_em": consultado_em,
        "mensagem": None,
    }

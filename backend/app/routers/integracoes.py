from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.errors import api_error
from app.integrations.bigquery_client import BigQueryIntegrationError
from app.schemas.integracao_bigquery import IntegracaoBigQueryResponse
from app.services.integracao_bigquery_service import consultar_e_armazenar

router = APIRouter(tags=["integracoes"])


@router.get(
    "/api/integracoes/protheus-bigquery/{codigo_protheus}",
    response_model=IntegracaoBigQueryResponse,
)
def consultar_protheus_bigquery(
    codigo_protheus: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consultar_e_armazenar(db, codigo_protheus, user["id"])
    except BigQueryIntegrationError as exc:
        db.rollback()
        raise api_error(
            503,
            "BIGQUERY_INDISPONIVEL",
            str(exc),
            ["codigo_protheus"],
        ) from exc

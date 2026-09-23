from datetime import datetime
from typing import Any

from pydantic import BaseModel


class IntegracaoBigQueryResponse(BaseModel):
    codigo_protheus: str
    integracao_ativa: bool
    registros_encontrados: dict[str, list[dict[str, Any]]]
    consultado_em: datetime
    mensagem: str | None = None

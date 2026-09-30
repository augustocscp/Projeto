from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EstadoConservacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str
    ativo: bool
    ordem_exibicao: int
    criado_em: datetime
    atualizado_em: datetime

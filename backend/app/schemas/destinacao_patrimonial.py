from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DestinacaoPatrimonialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool
    ordem_exibicao: int
    criado_em: datetime
    atualizado_em: datetime

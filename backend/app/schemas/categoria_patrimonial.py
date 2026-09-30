from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoriaPatrimonialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

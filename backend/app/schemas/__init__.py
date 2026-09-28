from app.schemas.categoria_patrimonial import CategoriaPatrimonialResponse
from app.schemas.destinacao_patrimonial import DestinacaoPatrimonialResponse
from app.schemas.estado_conservacao import EstadoConservacaoResponse
from app.schemas.patrimonio import (
    PatrimonioCreate,
    PatrimonioListResponse,
    PatrimonioResponse,
    PatrimonioUpdate,
)
from app.schemas.responsavel import ResponsavelResponse
from app.schemas.situacao_patrimonial import SituacaoPatrimonialResponse

__all__ = [
    "CategoriaPatrimonialResponse",
    "DestinacaoPatrimonialResponse",
    "EstadoConservacaoResponse",
    "PatrimonioCreate",
    "PatrimonioListResponse",
    "PatrimonioResponse",
    "PatrimonioUpdate",
    "ResponsavelResponse",
    "SituacaoPatrimonialResponse",
]

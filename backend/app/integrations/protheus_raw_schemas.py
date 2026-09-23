from dataclasses import dataclass
from typing import Any, TypedDict


class RegistroProtheusRaw(TypedDict, total=False):
    """Registro deliberadamente sem campos definidos até a entrega do schema oficial."""


RegistroRaw = dict[str, Any]


@dataclass(frozen=True)
class TabelaProtheusConfig:
    origem: str
    tabela: str
    campo_filtro: str

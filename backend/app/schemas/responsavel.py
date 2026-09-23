from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResponsavelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    codigo_re: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=255)
    cargo: str | None = Field(default=None, max_length=255)
    departamento_id: int
    gestor_responsavel_id: int | None = None


class ResponsavelUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    cargo: str | None = Field(default=None, max_length=255)
    departamento_id: int | None = None
    gestor_responsavel_id: int | None = None


class ResponsavelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_re: str
    nome: str
    cargo: str | None
    departamento_id: int
    gestor_responsavel_id: int | None
    origem_dados: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

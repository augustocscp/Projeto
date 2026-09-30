from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.integrations.normalizacao import normalizar_codigo_re


class ResponsavelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    codigo_re: str = Field(min_length=1, max_length=5)
    nome: str = Field(min_length=1, max_length=255)
    cargo: str | None = Field(default=None, max_length=255)
    departamento_id: int | None = None
    gestor_responsavel_id: int | None = None
    departamento_externo: str | None = Field(default=None, max_length=255)
    gestor_responsavel: str | None = Field(default=None, max_length=255)

    @field_validator("codigo_re")
    @classmethod
    def normalizar_re(cls, valor: str) -> str:
        return normalizar_codigo_re(valor)


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
    departamento_id: int | None
    gestor_responsavel_id: int | None
    departamento_externo: str | None
    gestor_responsavel: str | None
    consultado_em: datetime | None
    origem_dados: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

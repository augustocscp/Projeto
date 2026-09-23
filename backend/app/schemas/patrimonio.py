from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatrimonioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    codigo_protheus: str | None = Field(default=None, max_length=100)
    codigo_sap: str | None = Field(default=None, max_length=100)
    numero_plaqueta_fisica: str = Field(min_length=1, max_length=100)
    descricao: str = Field(min_length=1)
    categoria_id: int
    marca: str | None = Field(default=None, max_length=255)
    modelo: str | None = Field(default=None, max_length=255)
    fabricante: str | None = Field(default=None, max_length=255)
    numero_serie: str | None = Field(default=None, max_length=255)
    data_fim_garantia: date | None = None
    empresa_id: int
    filial_id: int
    departamento_id: int
    localizacao_id: int
    responsavel_id: int
    estado_conservacao_id: int
    situacao_id: int
    destinacao_id: int
    observacao: str | None = None
    data_baixa: date | None = None
    numero_patrimonio_anterior: str | None = Field(default=None, max_length=100)


class PatrimonioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    codigo_protheus: str | None = Field(default=None, max_length=100)
    codigo_sap: str | None = Field(default=None, max_length=100)
    numero_plaqueta_fisica: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = Field(default=None, min_length=1)
    categoria_id: int | None = None
    marca: str | None = Field(default=None, max_length=255)
    modelo: str | None = Field(default=None, max_length=255)
    fabricante: str | None = Field(default=None, max_length=255)
    numero_serie: str | None = Field(default=None, max_length=255)
    data_fim_garantia: date | None = None
    empresa_id: int | None = None
    filial_id: int | None = None
    departamento_id: int | None = None
    localizacao_id: int | None = None
    responsavel_id: int | None = None
    estado_conservacao_id: int | None = None
    situacao_id: int | None = None
    destinacao_id: int | None = None
    observacao: str | None = None
    data_baixa: date | None = None
    numero_patrimonio_anterior: str | None = Field(default=None, max_length=100)


class ReferenciaResponse(BaseModel):
    id: int
    nome: str
    codigo: str | None = None


class PatrimonioResponse(BaseModel):
    id: int
    numero_tombo: str
    codigo_protheus: str | None
    codigo_sap: str | None
    numero_plaqueta_fisica: str
    descricao: str
    categoria: ReferenciaResponse
    marca: str | None
    modelo: str | None
    fabricante: str | None
    numero_serie: str | None
    data_fim_garantia: date | None
    empresa: ReferenciaResponse
    filial: ReferenciaResponse
    departamento: ReferenciaResponse
    localizacao: ReferenciaResponse
    cidade: ReferenciaResponse
    responsavel: ReferenciaResponse
    estado_conservacao: ReferenciaResponse
    situacao: ReferenciaResponse
    destinacao: ReferenciaResponse
    observacao: str | None
    data_baixa: date | None
    numero_patrimonio_anterior: str | None
    protheus_status: str | None
    protheus_consultado_em: datetime | None
    criado_em: datetime
    atualizado_em: datetime
    ativo: bool


class PatrimonioListResponse(BaseModel):
    items: list[PatrimonioResponse]
    page: int
    page_size: int
    total: int
    pages: int

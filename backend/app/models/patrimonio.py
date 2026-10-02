from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DATABASE_SCHEMA
from app.database import Base

PATRIMONIO_NUMERO_TOMBO_SEQUENCE = Sequence(
    "patrimonio_numero_tombo_seq",
    schema=DATABASE_SCHEMA,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Patrimonio(Base):
    __tablename__ = "patrimonios"
    __table_args__ = (
        UniqueConstraint("numero_tombo", name="uq_patrimonios_numero_tombo"),
        UniqueConstraint(
            "numero_plaqueta_fisica", name="uq_patrimonios_numero_plaqueta_fisica"
        ),
        UniqueConstraint("codigo_protheus", "numero_item", name="uq_patrimonios_protheus_item"),
        CheckConstraint(
            "(possui_garantia AND data_fim_garantia IS NOT NULL) OR "
            "(NOT possui_garantia AND data_fim_garantia IS NULL)",
            name="ck_patrimonios_garantia_data",
        ),
        CheckConstraint(
            "data_fim_garantia IS NULL OR "
            "data_fim_garantia >= "
            "(data_cadastro AT TIME ZONE 'America/Sao_Paulo')::date",
            name="ck_patrimonios_garantia_data_cadastro",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero_tombo: Mapped[str] = mapped_column(
        String(30),
        index=True,
        server_default=PATRIMONIO_NUMERO_TOMBO_SEQUENCE.next_value(),
    )
    codigo_protheus: Mapped[str] = mapped_column(String(100), index=True)
    numero_item: Mapped[str] = mapped_column(String(100), index=True)
    codigo_sap: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    numero_plaqueta_fisica: Mapped[str] = mapped_column(String(100), index=True)
    numero_patrimonio_anterior: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    descricao: Mapped[str] = mapped_column(Text)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.categorias_patrimoniais.id"), index=True
    )
    marca: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modelo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fabricante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numero_serie: Mapped[str | None] = mapped_column(String(255), nullable=True)
    possui_garantia: Mapped[bool] = mapped_column(Boolean)
    codigo_produto: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_fim_garantia: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_baixa_origem: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.empresas.id"), index=True
    )
    filial_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.filiais.id"), index=True
    )
    departamento_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.departamentos.id"), index=True
    )
    localizacao_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.localizacoes.id"), index=True
    )
    responsavel_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.responsaveis.id"), index=True
    )
    estado_conservacao_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.estados_conservacao.id"), index=True
    )
    situacao_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.situacoes_patrimoniais.id"), index=True
    )
    destinacao_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.destinacoes_patrimoniais.id"), index=True
    )
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_baixa: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario_cadastro_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.usuarios.id"), index=True
    )
    data_cadastro: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    usuario_ultima_atualizacao_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.usuarios.id"), index=True
    )
    data_ultima_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    protheus_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    protheus_consultado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    protheus_atualizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dados_protheus_raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    categoria = relationship("CategoriaPatrimonial", back_populates="patrimonios")
    empresa = relationship("Empresa")
    filial = relationship("Filial")
    departamento = relationship("Departamento")
    localizacao = relationship("Localizacao")
    responsavel = relationship("Responsavel", back_populates="patrimonios")
    estado_conservacao = relationship("EstadoConservacao", back_populates="patrimonios")
    situacao = relationship("SituacaoPatrimonial", back_populates="patrimonios")
    destinacao = relationship("DestinacaoPatrimonial", back_populates="patrimonios")
    usuario_cadastro = relationship("Usuario", foreign_keys=[usuario_cadastro_id])
    usuario_ultima_atualizacao = relationship(
        "Usuario", foreign_keys=[usuario_ultima_atualizacao_id]
    )
    contabil = relationship("PatrimonioContabil", back_populates="patrimonio", uselist=False)

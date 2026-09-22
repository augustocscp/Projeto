from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DATABASE_SCHEMA
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Localizacao(Base):
    __tablename__ = "localizacoes"
    __table_args__ = (
        UniqueConstraint("nome", name="uq_localizacoes_nome"),
        CheckConstraint(
            "tipo IN ("
            "'SALA', 'BAIA', 'PATIO', 'TERMINAL', 'PORTAO', "
            "'BANHEIRO', 'ESTACIONAMENTO', 'DEPOSITO', "
            "'AREA_OPERACIONAL', 'OUTRO'"
            ")",
            name="ck_localizacoes_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nome: Mapped[str] = mapped_column(String(255), index=True)
    tipo: Mapped[str] = mapped_column(String(30))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    vinculos = relationship(
        "LocalizacaoVinculo",
        back_populates="localizacao",
        cascade="all, delete-orphan",
    )


class LocalizacaoVinculo(Base):
    __tablename__ = "localizacao_vinculos"
    __table_args__ = (
        UniqueConstraint(
            "localizacao_id",
            "filial_id",
            "departamento_id",
            name="uq_localizacao_vinculos_localizacao_filial_departamento",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    localizacao_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.localizacoes.id"),
        index=True,
    )
    filial_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.filiais.id"),
        index=True,
    )
    departamento_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.departamentos.id"),
        index=True,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    localizacao = relationship("Localizacao", back_populates="vinculos")
    filial = relationship("Filial", back_populates="localizacao_vinculos")
    departamento = relationship(
        "Departamento",
        back_populates="localizacao_vinculos",
    )

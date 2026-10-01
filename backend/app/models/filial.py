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


class Filial(Base):
    __tablename__ = "filiais"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nome"),
        CheckConstraint(
            "tipo_unidade IN ('TERMINAL', 'GARAGEM', 'ESCRITORIO')",
            name="ck_filiais_tipo_unidade",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.empresas.id"),
        index=True,
    )
    cidade_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.cidades.id"),
        index=True,
    )
    nome: Mapped[str] = mapped_column(String(255), index=True)
    tipo_unidade: Mapped[str] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    empresa = relationship("Empresa", back_populates="filiais")
    cidade = relationship("Cidade", back_populates="filiais")
    localizacao_vinculos = relationship(
        "LocalizacaoVinculo",
        back_populates="filial",
        cascade="all, delete-orphan",
    )

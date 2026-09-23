from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DATABASE_SCHEMA
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Responsavel(Base):
    __tablename__ = "responsaveis"
    __table_args__ = (
        UniqueConstraint("codigo_re", name="uq_responsaveis_codigo_re"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_re: Mapped[str] = mapped_column(String(50), index=True)
    nome: Mapped[str] = mapped_column(String(255), index=True)
    cargo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    departamento_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.departamentos.id"), index=True
    )
    gestor_responsavel_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.responsaveis.id"), nullable=True, index=True
    )
    origem_dados: Mapped[str] = mapped_column(String(30), default="MANUAL")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    departamento = relationship("Departamento")
    gestor_responsavel = relationship(
        "Responsavel", remote_side="Responsavel.id", back_populates="subordinados"
    )
    subordinados = relationship("Responsavel", back_populates="gestor_responsavel")
    patrimonios = relationship("Patrimonio", back_populates="responsavel")

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EstadoConservacao(Base):
    __tablename__ = "estados_conservacao"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_estados_conservacao_codigo"),
        UniqueConstraint("nome", name="uq_estados_conservacao_nome"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), index=True)
    nome: Mapped[str] = mapped_column(String(255), index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    ordem_exibicao: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    patrimonios = relationship("Patrimonio", back_populates="estado_conservacao")

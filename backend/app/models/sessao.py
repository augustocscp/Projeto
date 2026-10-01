from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DATABASE_SCHEMA
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Sessao(Base):
    __tablename__ = "sessoes"
    __table_args__ = (UniqueConstraint("token_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), index=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.usuarios.id"),
        index=True,
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ultimo_acesso_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    usuario = relationship("Usuario", back_populates="sessoes")

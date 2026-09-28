from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.config import DATABASE_SCHEMA
from app.database import Base


class HistoricoControlePatrimonial(Base):
    __tablename__ = "historico_controle_patrimonial"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patrimonio_id: Mapped[int] = mapped_column(ForeignKey(f"{DATABASE_SCHEMA}.patrimonios.id"), index=True)
    campo_alterado: Mapped[str] = mapped_column(String(100))
    valor_anterior: Mapped[str | None] = mapped_column(Text)
    valor_novo: Mapped[str | None] = mapped_column(Text)
    motivo: Mapped[str | None] = mapped_column(Text)
    usuario_id: Mapped[int] = mapped_column(ForeignKey(f"{DATABASE_SCHEMA}.usuarios.id"))
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

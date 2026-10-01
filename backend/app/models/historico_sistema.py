from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.config import DATABASE_SCHEMA
from app.database import Base


class HistoricoSistema(Base):
    __tablename__ = "historico_sistema"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patrimonio_id: Mapped[int | None] = mapped_column(ForeignKey(f"{DATABASE_SCHEMA}.patrimonios.id"), index=True)
    tipo_evento: Mapped[str] = mapped_column(String(50))
    descricao: Mapped[str] = mapped_column(Text)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey(f"{DATABASE_SCHEMA}.usuarios.id"))
    dados_contexto: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

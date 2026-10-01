from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DATABASE_SCHEMA
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IntegracaoBigQueryStaging(Base):
    __tablename__ = "integracao_bigquery_staging"
    __table_args__ = (
        CheckConstraint(
            "tabela_origem IN ('SN1', 'SN3', 'SNG')",
            name="ck_integracao_bigquery_staging_tabela_origem",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tabela_origem: Mapped[str] = mapped_column(String(10), index=True)
    codigo_protheus_consultado: Mapped[str] = mapped_column(String(100), index=True)
    dados_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    hash_registro: Mapped[str] = mapped_column(String(64), index=True)
    consultado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey(f"{DATABASE_SCHEMA}.usuarios.id"), index=True
    )
    processado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    usuario = relationship("Usuario")

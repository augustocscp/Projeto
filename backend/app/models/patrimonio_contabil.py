from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import DATABASE_SCHEMA
from app.database import Base


class PatrimonioContabil(Base):
    __tablename__ = "patrimonios_contabeis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patrimonio_id: Mapped[int] = mapped_column(ForeignKey(f"{DATABASE_SCHEMA}.patrimonios.id"), unique=True, index=True)
    numero_nota_fiscal: Mapped[str | None] = mapped_column(String(100))
    serie_nota_fiscal: Mapped[str | None] = mapped_column(String(100))
    data_nota_fiscal: Mapped[date | None] = mapped_column(Date)
    codigo_fornecedor: Mapped[str | None] = mapped_column(String(100))
    fornecedor: Mapped[str | None] = mapped_column(String(255))
    valor_aquisicao: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    icms: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    valor_atual: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    percentual_depreciacao: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    depreciacao_mensal: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    depreciacao_acumulada: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    inicio_depreciacao: Mapped[date | None] = mapped_column(Date)
    fim_depreciacao: Mapped[date | None] = mapped_column(Date)
    conta_contabil: Mapped[str | None] = mapped_column(String(100))
    centro_custo: Mapped[str | None] = mapped_column(String(100))
    data_baixa_sn1: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_baixa_sn3: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consultado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    dados_brutos_sn1: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    dados_brutos_sn3: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    patrimonio = relationship("Patrimonio", back_populates="contabil")

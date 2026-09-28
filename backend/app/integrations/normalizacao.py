from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation


def texto(valor):
    if valor is None:
        return None
    resultado = str(valor).strip()
    return resultado or None


def decimal(valor):
    if valor in (None, ""):
        return None
    try:
        return Decimal(str(valor).replace(",", "."))
    except InvalidOperation:
        return None


def data(valor):
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    bruto = str(valor).strip()
    for formato in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(bruto[:10], formato).date()
        except ValueError:
            continue
    return None


def instante(valor):
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
    dia = data(valor)
    return datetime.combine(dia, datetime.min.time(), timezone.utc) if dia else None

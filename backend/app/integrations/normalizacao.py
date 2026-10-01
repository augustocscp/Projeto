from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation


def texto(valor):
    if valor is None:
        return None
    resultado = str(valor).strip()
    return resultado or None


def normalizar_identificador(valor: str, tamanho: int, nome: str) -> str:
    codigo = texto(valor)
    if (
        codigo is None
        or not codigo.isascii()
        or not codigo.isalnum()
        or len(codigo) > tamanho
    ):
        raise ValueError(
            f"{nome} deve conter de 1 a {tamanho} letras ou numeros"
        )
    return codigo.upper().zfill(tamanho)


def normalizar_codigo_protheus(valor: str) -> str:
    return normalizar_identificador(valor, 10, "O codigo Protheus")


def normalizar_numero_item(valor: str) -> str:
    return normalizar_identificador(valor, 4, "O numero do item")


def normalizar_numero_plaqueta(valor: str) -> str:
    return normalizar_identificador(valor, 10, "O numero da plaqueta")


def normalizar_codigo_re(valor: str) -> str:
    return normalizar_identificador(valor, 5, "O codigo RE")


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

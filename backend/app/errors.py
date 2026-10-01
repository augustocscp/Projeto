from fastapi import HTTPException


def api_error(
    status_code: int,
    codigo: str,
    mensagem: str,
    campos: list[str] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "codigo": codigo,
            "mensagem": mensagem,
            "campos": campos or [],
        },
    )

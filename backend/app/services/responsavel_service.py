from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models.responsavel import Responsavel


def listar_responsaveis(db: Session, ativo: bool | None = True) -> list[Responsavel]:
    stmt = select(Responsavel).order_by(Responsavel.nome)
    if ativo is not None:
        stmt = stmt.where(Responsavel.ativo.is_(ativo))
    return list(db.scalars(stmt).all())


def validar_responsavel(db: Session, responsavel_id: int) -> Responsavel:
    responsavel = db.get(Responsavel, responsavel_id)
    if responsavel is None:
        raise api_error(
            404,
            "RESPONSAVEL_NAO_ENCONTRADO",
            "Responsável não encontrado.",
            ["responsavel_id"],
        )
    if not responsavel.ativo:
        raise api_error(
            422,
            "RESPONSAVEL_INATIVO",
            "O responsável informado está inativo.",
            ["responsavel_id"],
        )
    return responsavel

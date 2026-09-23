from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models.departamento import Departamento
from app.models.empresa import Empresa
from app.models.filial import Filial
from app.models.localizacao import Localizacao, LocalizacaoVinculo


def listar_localizacoes(
    db: Session, filial_id: int | None, departamento_id: int | None
) -> list[Localizacao]:
    stmt = (
        select(Localizacao)
        .join(LocalizacaoVinculo)
        .where(Localizacao.ativo.is_(True), LocalizacaoVinculo.ativo.is_(True))
        .distinct()
        .order_by(Localizacao.nome)
    )
    if filial_id is not None:
        stmt = stmt.where(LocalizacaoVinculo.filial_id == filial_id)
    if departamento_id is not None:
        stmt = stmt.where(LocalizacaoVinculo.departamento_id == departamento_id)
    return list(db.scalars(stmt).all())


def validar_localizacao(
    db: Session,
    empresa_id: int,
    filial_id: int,
    departamento_id: int,
    localizacao_id: int,
) -> tuple[Empresa, Filial, Departamento, Localizacao]:
    empresa = db.get(Empresa, empresa_id)
    filial = db.get(Filial, filial_id)
    departamento = db.get(Departamento, departamento_id)
    localizacao = db.get(Localizacao, localizacao_id)

    entidades = (
        (empresa, "EMPRESA_NAO_ENCONTRADA", "empresa_id"),
        (filial, "FILIAL_NAO_ENCONTRADA", "filial_id"),
        (departamento, "DEPARTAMENTO_NAO_ENCONTRADO", "departamento_id"),
        (localizacao, "LOCALIZACAO_NAO_ENCONTRADA", "localizacao_id"),
    )
    for entidade, codigo, campo in entidades:
        if entidade is None:
            raise api_error(404, codigo, "Recurso informado não encontrado.", [campo])
        if not entidade.ativo:
            raise api_error(422, f"{codigo.removesuffix('_NAO_ENCONTRADA')}_INATIVA", "Recurso informado está inativo.", [campo])

    if filial.empresa_id != empresa_id:
        raise api_error(
            422,
            "FILIAL_INVALIDA",
            "A filial não pertence à empresa informada.",
            ["empresa_id", "filial_id"],
        )

    vinculo = db.scalar(
        select(LocalizacaoVinculo).where(
            LocalizacaoVinculo.localizacao_id == localizacao_id,
            LocalizacaoVinculo.filial_id == filial_id,
            LocalizacaoVinculo.departamento_id == departamento_id,
            LocalizacaoVinculo.ativo.is_(True),
        )
    )
    if vinculo is None:
        raise api_error(
            422,
            "LOCALIZACAO_INVALIDA",
            "A localização não pertence à filial e ao departamento informados.",
            ["localizacao_id", "filial_id", "departamento_id"],
        )
    return empresa, filial, departamento, localizacao

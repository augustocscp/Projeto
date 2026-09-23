from datetime import datetime, timezone
from math import ceil

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.config import DATABASE_SCHEMA
from app.errors import api_error
from app.models.categoria_patrimonial import CategoriaPatrimonial
from app.models.destinacao_patrimonial import DestinacaoPatrimonial
from app.models.estado_conservacao import EstadoConservacao
from app.models.filial import Filial
from app.models.patrimonio import Patrimonio
from app.models.situacao_patrimonial import SituacaoPatrimonial
from app.schemas.patrimonio import PatrimonioCreate, PatrimonioUpdate
from app.services.localizacao_service import validar_localizacao
from app.services.responsavel_service import validar_responsavel


PATRIMONIO_LOAD_OPTIONS = (
    selectinload(Patrimonio.categoria),
    selectinload(Patrimonio.empresa),
    selectinload(Patrimonio.filial).selectinload(Filial.cidade),
    selectinload(Patrimonio.departamento),
    selectinload(Patrimonio.localizacao),
    selectinload(Patrimonio.responsavel),
    selectinload(Patrimonio.estado_conservacao),
    selectinload(Patrimonio.situacao),
    selectinload(Patrimonio.destinacao),
)


def _validar_dominio(db: Session, model, identificador: int, campo: str):
    registro = db.get(model, identificador)
    if registro is None:
        raise api_error(
            404,
            f"{campo.upper()}_NAO_ENCONTRADO",
            "Domínio patrimonial não encontrado.",
            [f"{campo}_id"],
        )
    if not registro.ativo:
        raise api_error(
            422,
            f"{campo.upper()}_INATIVO",
            "Domínio patrimonial está inativo.",
            [f"{campo}_id"],
        )
    return registro


def _validar_baixa(situacao: SituacaoPatrimonial, data_baixa) -> None:
    if situacao.codigo == "BAIXADO" and data_baixa is None:
        raise api_error(
            422,
            "DATA_BAIXA_OBRIGATORIA",
            "A data de baixa é obrigatória para patrimônio baixado.",
            ["situacao_id", "data_baixa"],
        )
    if situacao.codigo != "BAIXADO" and data_baixa is not None:
        raise api_error(
            422,
            "DATA_BAIXA_INVALIDA",
            "A data de baixa deve ser nula quando o patrimônio não está baixado.",
            ["situacao_id", "data_baixa"],
        )


def _proximo_numero_tombo(db: Session) -> str:
    valor = db.scalar(
        text(f"SELECT nextval('{DATABASE_SCHEMA}.patrimonio_numero_tombo_seq')")
    )
    return f"PAT-{valor:06d}"


def _carregar(db: Session, patrimonio_id: int) -> Patrimonio | None:
    return db.scalar(
        select(Patrimonio)
        .where(Patrimonio.id == patrimonio_id)
        .options(*PATRIMONIO_LOAD_OPTIONS)
    )


def obter_patrimonio(db: Session, patrimonio_id: int) -> Patrimonio:
    patrimonio = _carregar(db, patrimonio_id)
    if patrimonio is None:
        raise api_error(
            404,
            "PATRIMONIO_NAO_ENCONTRADO",
            "Patrimônio não encontrado.",
            ["patrimonio_id"],
        )
    return patrimonio


def _validar_referencias(db: Session, dados: dict) -> SituacaoPatrimonial:
    _validar_dominio(db, CategoriaPatrimonial, dados["categoria_id"], "categoria")
    _validar_dominio(
        db,
        EstadoConservacao,
        dados["estado_conservacao_id"],
        "estado_conservacao",
    )
    situacao = _validar_dominio(
        db, SituacaoPatrimonial, dados["situacao_id"], "situacao"
    )
    _validar_dominio(db, DestinacaoPatrimonial, dados["destinacao_id"], "destinacao")
    validar_localizacao(
        db,
        dados["empresa_id"],
        dados["filial_id"],
        dados["departamento_id"],
        dados["localizacao_id"],
    )
    validar_responsavel(db, dados["responsavel_id"])
    _validar_baixa(situacao, dados.get("data_baixa"))
    return situacao


def criar_patrimonio(
    db: Session, payload: PatrimonioCreate, usuario_id: int
) -> Patrimonio:
    dados = payload.model_dump()
    _validar_referencias(db, dados)
    if db.scalar(
        select(Patrimonio.id).where(
            Patrimonio.numero_plaqueta_fisica == dados["numero_plaqueta_fisica"]
        )
    ):
        raise api_error(
            409,
            "PLAQUETA_DUPLICADA",
            "Já existe patrimônio com a plaqueta física informada.",
            ["numero_plaqueta_fisica"],
        )

    agora = datetime.now(timezone.utc)
    patrimonio = Patrimonio(
        **dados,
        numero_tombo=_proximo_numero_tombo(db),
        usuario_cadastro_id=usuario_id,
        data_cadastro=agora,
        usuario_ultima_atualizacao_id=usuario_id,
        data_ultima_atualizacao=agora,
        ativo=True,
    )
    db.add(patrimonio)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            409,
            "CONFLITO_PATRIMONIO",
            "Não foi possível criar o patrimônio por conflito de dados.",
            ["numero_plaqueta_fisica"],
        ) from exc
    return obter_patrimonio(db, patrimonio.id)


def atualizar_patrimonio(
    db: Session,
    patrimonio_id: int,
    payload: PatrimonioUpdate,
    usuario_id: int,
) -> Patrimonio:
    patrimonio = obter_patrimonio(db, patrimonio_id)
    alteracoes = payload.model_dump(exclude_unset=True)
    if not alteracoes:
        return patrimonio

    campos_movimento = {"empresa_id", "filial_id", "departamento_id", "localizacao_id"}
    movimentado = any(
        campo in alteracoes and alteracoes[campo] != getattr(patrimonio, campo)
        for campo in campos_movimento
    )
    if patrimonio.situacao.codigo == "BAIXADO" and movimentado:
        raise api_error(
            409,
            "PATRIMONIO_BAIXADO",
            "Patrimônio baixado não pode ser movimentado.",
            sorted(campos_movimento),
        )

    finais = {
        campo: alteracoes.get(campo, getattr(patrimonio, campo))
        for campo in (
            "categoria_id",
            "estado_conservacao_id",
            "situacao_id",
            "destinacao_id",
            "empresa_id",
            "filial_id",
            "departamento_id",
            "localizacao_id",
            "responsavel_id",
            "data_baixa",
        )
    }
    _validar_referencias(db, finais)

    if alteracoes.get("numero_plaqueta_fisica") is None and "numero_plaqueta_fisica" in alteracoes:
        raise api_error(422, "PLAQUETA_OBRIGATORIA", "A plaqueta física é obrigatória.", ["numero_plaqueta_fisica"])
    if alteracoes.get("descricao") is None and "descricao" in alteracoes:
        raise api_error(422, "DESCRICAO_OBRIGATORIA", "A descrição é obrigatória.", ["descricao"])

    for campo, valor in alteracoes.items():
        setattr(patrimonio, campo, valor)
    patrimonio.usuario_ultima_atualizacao_id = usuario_id
    patrimonio.data_ultima_atualizacao = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            409,
            "CONFLITO_PATRIMONIO",
            "Não foi possível atualizar o patrimônio por conflito de dados.",
            ["numero_plaqueta_fisica"],
        ) from exc
    return obter_patrimonio(db, patrimonio_id)


def inativar_patrimonio(
    db: Session, patrimonio_id: int, usuario_id: int
) -> Patrimonio:
    patrimonio = obter_patrimonio(db, patrimonio_id)
    patrimonio.ativo = False
    patrimonio.usuario_ultima_atualizacao_id = usuario_id
    patrimonio.data_ultima_atualizacao = datetime.now(timezone.utc)
    db.commit()
    return obter_patrimonio(db, patrimonio_id)


def listar_patrimonios(
    db: Session,
    page: int,
    page_size: int,
    filtros: dict,
) -> dict:
    criterios = []
    for campo in (
        "situacao_id",
        "categoria_id",
        "filial_id",
        "departamento_id",
        "localizacao_id",
        "responsavel_id",
        "ativo",
    ):
        if filtros.get(campo) is not None:
            criterios.append(getattr(Patrimonio, campo) == filtros[campo])
    for campo in ("numero_tombo", "codigo_protheus", "numero_plaqueta_fisica"):
        if filtros.get(campo):
            criterios.append(getattr(Patrimonio, campo).ilike(f"%{filtros[campo]}%"))

    total = db.scalar(select(func.count(Patrimonio.id)).where(*criterios)) or 0
    stmt = (
        select(Patrimonio)
        .where(*criterios)
        .options(*PATRIMONIO_LOAD_OPTIONS)
        .order_by(Patrimonio.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "items": list(db.scalars(stmt).all()),
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": ceil(total / page_size) if total else 0,
    }


def resumo_patrimonial(db: Session) -> dict:
    total = db.scalar(select(func.count(Patrimonio.id))) or 0
    ativos = db.scalar(
        select(func.count(Patrimonio.id)).where(Patrimonio.ativo.is_(True))
    ) or 0
    baixados = db.scalar(
        select(func.count(Patrimonio.id))
        .join(SituacaoPatrimonial)
        .where(SituacaoPatrimonial.codigo == "BAIXADO", Patrimonio.ativo.is_(True))
    ) or 0
    por_situacao = {
        nome: quantidade
        for nome, quantidade in db.execute(
            select(SituacaoPatrimonial.nome, func.count(Patrimonio.id))
            .outerjoin(Patrimonio)
            .group_by(SituacaoPatrimonial.id, SituacaoPatrimonial.nome)
            .order_by(SituacaoPatrimonial.ordem_exibicao)
        ).all()
    }
    return {
        "bensCadastrados": total,
        "bensAtivos": ativos,
        "bensInativos": total - ativos,
        "bensBaixados": baixados,
        "porSituacao": por_situacao,
    }


def patrimonio_response(patrimonio: Patrimonio) -> dict:
    def referencia(objeto, codigo_attr: str = "codigo") -> dict:
        return {
            "id": objeto.id,
            "nome": objeto.nome,
            "codigo": getattr(objeto, codigo_attr, None),
        }

    return {
        "id": patrimonio.id,
        "numero_tombo": patrimonio.numero_tombo,
        "codigo_protheus": patrimonio.codigo_protheus,
        "codigo_sap": patrimonio.codigo_sap,
        "numero_plaqueta_fisica": patrimonio.numero_plaqueta_fisica,
        "descricao": patrimonio.descricao,
        "categoria": referencia(patrimonio.categoria),
        "marca": patrimonio.marca,
        "modelo": patrimonio.modelo,
        "fabricante": patrimonio.fabricante,
        "numero_serie": patrimonio.numero_serie,
        "data_fim_garantia": patrimonio.data_fim_garantia,
        "empresa": referencia(patrimonio.empresa),
        "filial": referencia(patrimonio.filial),
        "departamento": referencia(patrimonio.departamento),
        "localizacao": referencia(patrimonio.localizacao),
        "cidade": referencia(patrimonio.filial.cidade),
        "responsavel": referencia(patrimonio.responsavel, "codigo_re"),
        "estado_conservacao": referencia(patrimonio.estado_conservacao),
        "situacao": referencia(patrimonio.situacao),
        "destinacao": referencia(patrimonio.destinacao),
        "observacao": patrimonio.observacao,
        "data_baixa": patrimonio.data_baixa,
        "numero_patrimonio_anterior": patrimonio.numero_patrimonio_anterior,
        "protheus_status": patrimonio.protheus_status,
        "protheus_consultado_em": patrimonio.protheus_consultado_em,
        "criado_em": patrimonio.data_cadastro,
        "atualizado_em": patrimonio.data_ultima_atualizacao,
        "ativo": patrimonio.ativo,
    }

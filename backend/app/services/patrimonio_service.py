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
from app.config import GCP_BIGQUERY_ENABLED
from app.integrations.protheus_patrimonio_service import ProtheusPatrimonioService
from app.integrations.protheus_contabil_service import ProtheusContabilService
from app.integrations.bigquery_client import BigQueryIntegrationError
from app.models.patrimonio_contabil import PatrimonioContabil
from app.services.localizacao_service import validar_localizacao
from app.services.responsavel_service import resolver_responsavel
from app.services.historico_service import registrar_alteracoes_controle, registrar_evento

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
    selectinload(Patrimonio.contabil),
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


SITUACOES_BAIXA = {"BAIXADO", "ALIENADO", "EXTRAVIADO", "SINISTRADO"}


def _validar_baixa(situacao: SituacaoPatrimonial, data_baixa_origem) -> None:
    if data_baixa_origem is not None and situacao.codigo not in SITUACOES_BAIXA:
        raise api_error(422, "SITUACAO_INCOMPATIVEL_COM_BAIXA",
                        "A situação deve ser compatível com a baixa informada pelo Protheus.", ["situacao_id"])


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
    _validar_baixa(situacao, dados.get("data_baixa_origem"))
    return situacao


def criar_patrimonio(
        db: Session, payload: PatrimonioCreate, usuario_id: int
) -> Patrimonio:
    dados = payload.model_dump()
    codigo_re = dados.pop("codigo_re")
    responsavel = resolver_responsavel(db, codigo_re, usuario_id)
    dados["responsavel_id"] = responsavel.id
    contabil_dados = None
    if GCP_BIGQUERY_ENABLED:
        try:
            cadastral = ProtheusPatrimonioService().consultar(dados["codigo_protheus"], dados["numero_item"])
            contabil_dados = ProtheusContabilService().consultar(dados["codigo_protheus"], dados["numero_item"])
        except BigQueryIntegrationError as exc:
            registrar_evento(db, "FALHA_INTEGRACAO", "Falha técnica na consulta de criação.", usuario_id=usuario_id)
            db.commit()
            raise api_error(503, "INTEGRACAO_INDISPONIVEL", "Integração com o Protheus indisponível.") from exc
        if cadastral is None:
            raise api_error(404, "PATRIMONIO_PROTHEUS_NAO_ENCONTRADO", "Bem não encontrado no Protheus.",
                            ["codigo_protheus", "numero_item"])
        for campo in ("codigo_produto", "descricao", "modelo", "fabricante"):
            dados[campo] = cadastral.get(campo)
        if contabil_dados:
            dados["data_baixa_origem"] = contabil_dados.get("data_baixa_sn1")
    if not dados.get("descricao"):
        raise api_error(422, "DESCRICAO_OBRIGATORIA",
                        "Descrição não obtida do Protheus; informe-a para cadastro com integração inativa.",
                        ["descricao"])
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
    if contabil_dados:
        extras = {"multiplos_sn3", "divergencia_baixa"}
        snapshot = PatrimonioContabil(patrimonio_id=patrimonio.id,
                                      **{k: v for k, v in contabil_dados.items() if k not in extras})
        db.add(snapshot)
        if contabil_dados.get("multiplos_sn3"):
            registrar_evento(db, "FALHA_INTEGRACAO",
                             "Mais de um registro N3_TIPO='10' encontrado; utilizado o primeiro.",
                             patrimonio_id=patrimonio.id, usuario_id=usuario_id)
        if contabil_dados.get("divergencia_baixa"):
            registrar_evento(db, "DIVERGENCIA_BAIXA", "Divergência entre as informações de baixa da SN1 e SN3.",
                             patrimonio_id=patrimonio.id, usuario_id=usuario_id)
    registrar_evento(db, "CRIACAO", "Patrimônio criado.", patrimonio_id=patrimonio.id, usuario_id=usuario_id)
    db.commit()
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

    for campo in ("codigo_protheus", "numero_item", "numero_serie"):
        if campo in alteracoes and alteracoes[campo] is None:
            raise api_error(422, "CAMPO_OBRIGATORIO", "Campo obrigatório não pode ser nulo.", [campo])

    codigo_re = alteracoes.pop("codigo_re", None)
    if codigo_re is not None:
        alteracoes["responsavel_id"] = resolver_responsavel(db, codigo_re, usuario_id, patrimonio_id).id
    campos_movimento = {"empresa_id", "filial_id", "departamento_id", "localizacao_id", "responsavel_id"}
    movimentado = any(
        campo in alteracoes and alteracoes[campo] != getattr(patrimonio, campo)
        for campo in campos_movimento
    )
    if (patrimonio.data_baixa_origem is not None or patrimonio.situacao.codigo in SITUACOES_BAIXA) and movimentado:
        raise api_error(
            409,
            "PATRIMONIO_BAIXADO_NAO_MOVIMENTAVEL",
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
            "data_baixa_origem",
        )
    }
    _validar_referencias(db, finais)

    garantia = alteracoes.get("possui_garantia", patrimonio.possui_garantia)
    data_garantia = alteracoes.get("data_fim_garantia", patrimonio.data_fim_garantia)
    if garantia != (data_garantia is not None):
        raise api_error(422, "GARANTIA_INVALIDA", "Data de garantia inconsistente com possui_garantia.",
                        ["possui_garantia", "data_fim_garantia"])

    if alteracoes.get("numero_plaqueta_fisica") is None and "numero_plaqueta_fisica" in alteracoes:
        raise api_error(422, "PLAQUETA_OBRIGATORIA", "A plaqueta física é obrigatória.", ["numero_plaqueta_fisica"])
    if alteracoes.get("descricao") is None and "descricao" in alteracoes:
        raise api_error(422, "DESCRICAO_OBRIGATORIA", "A descrição é obrigatória.", ["descricao"])

    anterior = {campo: getattr(patrimonio, campo) for campo in alteracoes}
    for campo, valor in alteracoes.items():
        setattr(patrimonio, campo, valor)
    registrar_alteracoes_controle(db, patrimonio_id, usuario_id, anterior, alteracoes)
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
    registrar_evento(db, "INATIVACAO", "Patrimônio inativado.", patrimonio_id=patrimonio_id, usuario_id=usuario_id)
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
        "numero_item": patrimonio.numero_item,
        "codigo_sap": patrimonio.codigo_sap,
        "numero_plaqueta_fisica": patrimonio.numero_plaqueta_fisica,
        "descricao": patrimonio.descricao,
        "categoria": referencia(patrimonio.categoria),
        "marca": patrimonio.marca,
        "modelo": patrimonio.modelo,
        "fabricante": patrimonio.fabricante,
        "numero_serie": patrimonio.numero_serie,
        "possui_garantia": patrimonio.possui_garantia,
        "codigo_produto": patrimonio.codigo_produto,
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
        "data_baixa_origem": patrimonio.data_baixa_origem,
        "numero_patrimonio_anterior": patrimonio.numero_patrimonio_anterior,
        "protheus_status": patrimonio.protheus_status,
        "protheus_consultado_em": patrimonio.protheus_consultado_em,
        "criado_em": patrimonio.data_cadastro,
        "atualizado_em": patrimonio.data_ultima_atualizacao,
        "ativo": patrimonio.ativo,
        "contabil": contabil_response(patrimonio.contabil),
        "contabil_em_cache": True,
    }


def contabil_response(snapshot: PatrimonioContabil | None) -> dict | None:
    if snapshot is None:
        return None
    return {campo: getattr(snapshot, campo) for campo in (
        "numero_nota_fiscal", "serie_nota_fiscal", "data_nota_fiscal", "codigo_fornecedor", "fornecedor",
        "valor_aquisicao", "icms", "valor_atual", "percentual_depreciacao", "depreciacao_mensal",
        "depreciacao_acumulada", "inicio_depreciacao", "fim_depreciacao", "conta_contabil", "centro_custo",
        "data_baixa_sn1", "data_baixa_sn3", "consultado_em")}

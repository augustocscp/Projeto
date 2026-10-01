from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.historico_contabil import HistoricoContabil
from app.models.historico_controle_patrimonial import HistoricoControlePatrimonial
from app.models.historico_sistema import HistoricoSistema


def _texto(valor: Any) -> str | None:
    return None if valor is None else str(valor)


def registrar_evento(db: Session, tipo: str, descricao: str, *, patrimonio_id: int | None = None,
                     usuario_id: int | None = None, contexto: dict | None = None) -> None:
    db.add(HistoricoSistema(patrimonio_id=patrimonio_id, tipo_evento=tipo, descricao=descricao,
                            usuario_id=usuario_id, dados_contexto=contexto))


def registrar_alteracoes_controle(db: Session, patrimonio_id: int, usuario_id: int,
                                  anterior: dict, alteracoes: dict, motivo: str | None = None) -> None:
    for campo, novo in alteracoes.items():
        antigo = anterior.get(campo)
        if antigo != novo:
            db.add(HistoricoControlePatrimonial(
                patrimonio_id=patrimonio_id, campo_alterado=campo,
                valor_anterior=_texto(antigo), valor_novo=_texto(novo),
                motivo=motivo, usuario_id=usuario_id,
            ))


def historico_agregado(db: Session, patrimonio_id: int) -> dict:
    contabil = db.scalars(select(HistoricoContabil).where(HistoricoContabil.patrimonio_id == patrimonio_id).order_by(
        HistoricoContabil.id.desc())).all()
    controle = db.scalars(select(HistoricoControlePatrimonial).where(
        HistoricoControlePatrimonial.patrimonio_id == patrimonio_id).order_by(
        HistoricoControlePatrimonial.id.desc())).all()
    sistema = db.scalars(select(HistoricoSistema).where(HistoricoSistema.patrimonio_id == patrimonio_id).order_by(
        HistoricoSistema.id.desc())).all()
    return {
        "contabil": [
            {"campo_alterado": x.campo_alterado, "valor_anterior": x.valor_anterior, "valor_novo": x.valor_novo,
             "origem": x.origem, "usuario_id": x.usuario_id, "consultado_em": x.consultado_em} for x in contabil],
        "controle_patrimonial": [
            {"campo_alterado": x.campo_alterado, "valor_anterior": x.valor_anterior, "valor_novo": x.valor_novo,
             "motivo": x.motivo, "usuario_id": x.usuario_id, "data_hora": x.data_hora} for x in controle],
        "sistema": [{"tipo_evento": x.tipo_evento, "descricao": x.descricao, "usuario_id": x.usuario_id,
                     "dados_contexto": x.dados_contexto, "data_hora": x.data_hora} for x in sistema],
    }

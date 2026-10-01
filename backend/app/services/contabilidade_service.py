from sqlalchemy.orm import Session

from app.config import GCP_BIGQUERY_ENABLED
from app.integrations.protheus_contabil_service import ProtheusContabilService
from app.models.historico_contabil import HistoricoContabil
from app.models.patrimonio import Patrimonio
from app.models.patrimonio_contabil import PatrimonioContabil
from app.services.historico_service import registrar_evento

CAMPOS = (
    "numero_nota_fiscal", "serie_nota_fiscal", "data_nota_fiscal", "codigo_fornecedor",
    "fornecedor", "valor_aquisicao", "icms", "valor_atual", "percentual_depreciacao",
    "depreciacao_mensal", "depreciacao_acumulada", "inicio_depreciacao", "fim_depreciacao",
    "conta_contabil", "centro_custo", "data_baixa_sn1", "data_baixa_sn3",
)


def atualizar_snapshot(db: Session, patrimonio: Patrimonio, usuario_id: int | None,
                       service: ProtheusContabilService | None = None) -> tuple[PatrimonioContabil | None, bool]:
    snapshot = patrimonio.contabil
    if not GCP_BIGQUERY_ENABLED:
        return snapshot, True
    try:
        dados = (service or ProtheusContabilService()).consultar(patrimonio.codigo_protheus, patrimonio.numero_item)
    except Exception:
        registrar_evento(db, "FALHA_INTEGRACAO", "Falha ao atualizar dados contábeis do BigQuery.",
                         patrimonio_id=patrimonio.id, usuario_id=usuario_id)
        db.commit()
        return snapshot, True
    if dados is None:
        registrar_evento(db, "FALHA_INTEGRACAO", "Bem não encontrado na consulta contábil do BigQuery.",
                         patrimonio_id=patrimonio.id, usuario_id=usuario_id)
        db.commit()
        return snapshot, True
    if dados.pop("multiplos_sn3"):
        registrar_evento(db, "FALHA_INTEGRACAO",
                         "Mais de um registro contábil N3_TIPO='10' encontrado; utilizado o primeiro.",
                         patrimonio_id=patrimonio.id, usuario_id=usuario_id)
    if dados.pop("divergencia_baixa"):
        registrar_evento(db, "DIVERGENCIA_BAIXA", "Divergência entre as informações de baixa da SN1 e SN3.",
                         patrimonio_id=patrimonio.id, usuario_id=usuario_id)

    if snapshot is None:
        snapshot = PatrimonioContabil(patrimonio_id=patrimonio.id)
        db.add(snapshot)
    else:
        for campo in CAMPOS:
            antigo, novo = getattr(snapshot, campo), dados.get(campo)
            if antigo != novo:
                db.add(HistoricoContabil(patrimonio_id=patrimonio.id, campo_alterado=campo,
                                         valor_anterior=None if antigo is None else str(antigo),
                                         valor_novo=None if novo is None else str(novo), origem="API",
                                         usuario_id=usuario_id, consultado_em=dados["consultado_em"]))
    for campo in CAMPOS + ("consultado_em", "dados_brutos_sn1", "dados_brutos_sn3"):
        setattr(snapshot, campo, dados.get(campo))
    patrimonio.data_baixa_origem = dados.get("data_baixa_sn1")
    registrar_evento(db, "ATUALIZACAO_API", "Snapshot contábil atualizado pelo BigQuery.", patrimonio_id=patrimonio.id,
                     usuario_id=usuario_id)
    db.commit()
    db.refresh(snapshot)
    return snapshot, False

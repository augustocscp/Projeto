from datetime import datetime, timezone
from app.config import BIGQUERY_TABLE_SN1, BIGQUERY_TABLE_SN3
from app.integrations.bigquery_client import BigQueryClient, BigQueryConfigurationError
from app.integrations.normalizacao import data, decimal, instante, texto


class ProtheusContabilService:
    def __init__(self, client: BigQueryClient | None = None):
        self.client = client or BigQueryClient()

    def consultar(self, codigo_protheus: str, numero_item: str) -> dict | None:
        if not BIGQUERY_TABLE_SN1 or not BIGQUERY_TABLE_SN3:
            raise BigQueryConfigurationError("Tabelas SN1/SN3 não configuradas")
        sn1_linhas = self.client.consultar_tabela(BIGQUERY_TABLE_SN1,
                                                  {"N1_CBASE": codigo_protheus, "N1_ITEM": numero_item})
        if not sn1_linhas:
            return None
        # N3_TIPO='10' é parte invariável de toda consulta contábil.
        sn3_linhas = self.client.consultar_tabela(BIGQUERY_TABLE_SN3,
                                                  {"N3_CBASE": codigo_protheus, "N3_ITEM": numero_item,
                                                   "N3_TIPO": "10"})
        sn1, sn3 = sn1_linhas[0], (sn3_linhas[0] if sn3_linhas else {})
        valor_aquisicao = decimal(sn1.get("N1_VLAQUIS"))
        if valor_aquisicao is None:
            valor_aquisicao = decimal(sn3.get("N3_VORIG1"))
        acumulada = decimal(sn3.get("N3_VRDACM1"))
        baixa_sn1 = instante(sn1.get("N1_BAIXA"))
        baixa_sn3 = instante(sn3.get("N3_DTBAIXA") or sn3.get("N3_BAIXA"))
        return {
            "numero_nota_fiscal": texto(sn1.get("N1_NFISCAL")), "serie_nota_fiscal": texto(sn1.get("N1_NSERIE")),
            "data_nota_fiscal": data(sn1.get("N1_AQUISIC")), "codigo_fornecedor": texto(sn1.get("N1_FORNEC")),
            "fornecedor": texto(sn1.get("N1_LOJA")), "valor_aquisicao": valor_aquisicao,
            "icms": decimal(sn1.get("N1_ICMSAPR")),
            "valor_atual": valor_aquisicao - acumulada if valor_aquisicao is not None and acumulada is not None else None,
            "percentual_depreciacao": decimal(sn3.get("N3_TXDEPR1")),
            "depreciacao_mensal": decimal(sn3.get("N3_VRDMES1")),
            "depreciacao_acumulada": acumulada, "inicio_depreciacao": data(sn3.get("N3_DINDEPR")),
            "fim_depreciacao": data(sn3.get("N3_FIMDEPR")), "conta_contabil": texto(sn3.get("N3_CCONTAB")),
            "centro_custo": texto(sn3.get("N3_CUSTBEM")), "data_baixa_sn1": baixa_sn1, "data_baixa_sn3": baixa_sn3,
            "consultado_em": datetime.now(timezone.utc), "dados_brutos_sn1": sn1, "dados_brutos_sn3": sn3,
            "multiplos_sn3": len(sn3_linhas) > 1, "divergencia_baixa": (baixa_sn1 is None) != (baixa_sn3 is None),
        }

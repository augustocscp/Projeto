from app.config import BIGQUERY_TABLE_SB1, BIGQUERY_TABLE_SN1
from app.integrations.bigquery_client import BigQueryClient, BigQueryConfigurationError
from app.integrations.normalizacao import texto


class ProtheusPatrimonioService:
    def __init__(self, client: BigQueryClient | None = None):
        self.client = client or BigQueryClient()

    def consultar(self, codigo_protheus: str, numero_item: str) -> dict | None:
        if not BIGQUERY_TABLE_SN1 or not BIGQUERY_TABLE_SB1:
            raise BigQueryConfigurationError("Tabelas SN1/SB1 não configuradas")
        linhas = self.client.consultar_tabela(BIGQUERY_TABLE_SN1, {"N1_CBASE": codigo_protheus, "N1_ITEM": numero_item})
        if not linhas:
            return None
        sn1 = linhas[0]
        codigo_produto = texto(sn1.get("N1_PRODUTO"))
        sb1_linhas = self.client.consultar_tabela(BIGQUERY_TABLE_SB1,
                                                  {"B1_COD": codigo_produto}) if codigo_produto else []
        sb1 = sb1_linhas[0] if sb1_linhas else {}
        return {"codigo_produto": codigo_produto, "descricao": texto(sn1.get("N1_DESCRIC")),
                "modelo": texto(sb1.get("B1_MODELO")), "fabricante": texto(sb1.get("B1_FABRIC")),
                "dados_brutos_sn1": sn1, "dados_brutos_sb1": sb1}

from app.config import BIGQUERY_TABLE_CTT, BIGQUERY_TABLE_FUNCIONARIOS
from app.integrations.bigquery_client import BigQueryClient, BigQueryConfigurationError
from app.integrations.normalizacao import texto


def _texto_livre(valor):
    return valor if isinstance(valor, str) and valor != "" else None


class ProtheusResponsavelService:
    def __init__(self, client: BigQueryClient | None = None):
        self.client = client or BigQueryClient()

    def consultar(self, codigo_re: str) -> dict:
        if not BIGQUERY_TABLE_FUNCIONARIOS or not BIGQUERY_TABLE_CTT:
            raise BigQueryConfigurationError("Tabelas de responsáveis não configuradas")
        ativos = self.client.consultar_tabela(BIGQUERY_TABLE_FUNCIONARIOS,
                                              {"MATRICULA": codigo_re, "IS_CURRENT": True, "CODSITUACAO": "A"})
        if not ativos:
            diagnostico = self.client.consultar_tabela(BIGQUERY_TABLE_FUNCIONARIOS,
                                                       {"MATRICULA": codigo_re, "IS_CURRENT": True})
            return {"status": "inativo" if diagnostico else "nao_encontrado", "multiplos_current": len(diagnostico) > 1}
        funcionario = ativos[0]
        setor = texto(funcionario.get("DESCRICAO_SETOR"))
        centros = self.client.consultar_tabela(BIGQUERY_TABLE_CTT, {"CTT_DESC01": setor}) if setor else []
        centro = centros[0] if centros else {}
        return {"status": "ativo", "nome": texto(funcionario.get("NOMEFUNCIONARIO")),
                "cargo": texto(funcionario.get("CARGO")),
                "departamento_externo": _texto_livre(centro.get("CTT_XEQUIP")),
                "gestor_responsavel": _texto_livre(centro.get("CTT_XRESPO")),
                "ctt_encontrado": bool(centros), "multiplos_current": len(ativos) > 1}

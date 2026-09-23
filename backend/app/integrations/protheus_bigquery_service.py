from app.config import (
    BIGQUERY_FILTER_FIELD_SN1,
    BIGQUERY_FILTER_FIELD_SN3,
    BIGQUERY_FILTER_FIELD_SNG,
    BIGQUERY_TABLE_SN1,
    BIGQUERY_TABLE_SN3,
    BIGQUERY_TABLE_SNG,
)
from app.integrations.bigquery_client import (
    BigQueryClient,
    BigQueryConfigurationError,
)
from app.integrations.protheus_raw_schemas import RegistroRaw, TabelaProtheusConfig


class ProtheusBigQueryService:
    """Orquestra consultas independentes sem presumir joins ou campos de negócio."""

    def __init__(self, client: BigQueryClient | None = None) -> None:
        self.client = client or BigQueryClient()
        self.tabelas = (
            TabelaProtheusConfig("SN1", BIGQUERY_TABLE_SN1, BIGQUERY_FILTER_FIELD_SN1),
            TabelaProtheusConfig("SN3", BIGQUERY_TABLE_SN3, BIGQUERY_FILTER_FIELD_SN3),
            TabelaProtheusConfig("SNG", BIGQUERY_TABLE_SNG, BIGQUERY_FILTER_FIELD_SNG),
        )

    def consultar_codigo(self, codigo_protheus: str) -> dict[str, list[RegistroRaw]]:
        resultado: dict[str, list[RegistroRaw]] = {}
        for config in self.tabelas:
            if not config.tabela or not config.campo_filtro:
                raise BigQueryConfigurationError(
                    f"Tabela ou campo de filtro de {config.origem} não configurado"
                )
            resultado[config.origem] = self.client.consultar_tabela(
                config.tabela,
                {config.campo_filtro: codigo_protheus},
            )
        return resultado

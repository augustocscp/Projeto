import json
import re
from typing import Any

from app.config import (
    BIGQUERY_QUERY_TIMEOUT_SECONDS,
    GCP_BIGQUERY_DATASET,
    GCP_CREDENTIALS_PATH,
    GCP_PROJECT_ID,
)


class BigQueryIntegrationError(RuntimeError):
    pass


class BigQueryConfigurationError(BigQueryIntegrationError):
    pass


class BigQueryUnavailableError(BigQueryIntegrationError):
    pass


_TABLE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){0,2}$")
_FIELD_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class BigQueryClient:
    """Acesso genérico ao BigQuery, sem mapeamento de campos do Protheus."""

    def __init__(self) -> None:
        self.project_id = GCP_PROJECT_ID
        self.dataset = GCP_BIGQUERY_DATASET
        self.credentials_path = GCP_CREDENTIALS_PATH
        self.timeout = BIGQUERY_QUERY_TIMEOUT_SECONDS

    def _nome_tabela_completo(self, tabela: str) -> str:
        if not _TABLE_PATTERN.fullmatch(tabela):
            raise BigQueryConfigurationError("Identificador de tabela BigQuery inválido")

        partes = tabela.split(".")
        if len(partes) == 3:
            return tabela
        if len(partes) == 2 and self.project_id:
            return f"{self.project_id}.{tabela}"
        if len(partes) == 1 and self.project_id and self.dataset:
            return f"{self.project_id}.{self.dataset}.{tabela}"
        raise BigQueryConfigurationError(
            "Projeto, dataset e tabela do BigQuery não estão completamente configurados"
        )

    def _criar_cliente(self):
        try:
            from google.cloud import bigquery
        except ImportError as exc:
            raise BigQueryConfigurationError(
                "Dependência google-cloud-bigquery não instalada"
            ) from exc

        credentials = None
        if self.credentials_path:
            try:
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
            except Exception as exc:
                raise BigQueryConfigurationError(
                    "Não foi possível carregar as credenciais configuradas"
                ) from exc
        return bigquery.Client(project=self.project_id or None, credentials=credentials)

    def consultar_tabela(
        self, tabela: str, filtros: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not filtros:
            raise BigQueryConfigurationError(
                "Consultas sem filtro não são permitidas nesta integração"
            )

        try:
            from google.api_core.exceptions import (
                DeadlineExceeded,
                Forbidden,
                GoogleAPIError,
                NotFound,
                Unauthorized,
            )
            from google.cloud import bigquery

            tabela_completa = self._nome_tabela_completo(tabela)
            clausulas: list[str] = []
            parametros = []
            for indice, (campo, valor) in enumerate(filtros.items()):
                if not _FIELD_PATTERN.fullmatch(campo):
                    raise BigQueryConfigurationError(
                        "Identificador de campo BigQuery inválido"
                    )
                parametro = f"filtro_{indice}"
                clausulas.append(f"`{campo}` = @{parametro}")
                parametros.append(
                    bigquery.ScalarQueryParameter(parametro, "STRING", str(valor))
                )

            sql = (
                f"SELECT * FROM `{tabela_completa}` WHERE "
                + " AND ".join(clausulas)
            )
            job_config = bigquery.QueryJobConfig(query_parameters=parametros)
            rows = self._criar_cliente().query(sql, job_config=job_config).result(
                timeout=self.timeout
            )
            return [
                json.loads(
                    json.dumps(dict(row.items()), ensure_ascii=False, default=str)
                )
                for row in rows
            ]
        except BigQueryIntegrationError:
            raise
        except DeadlineExceeded as exc:
            raise BigQueryUnavailableError("Tempo limite da consulta excedido") from exc
        except NotFound as exc:
            raise BigQueryUnavailableError("Tabela BigQuery não encontrada") from exc
        except (Forbidden, Unauthorized) as exc:
            raise BigQueryUnavailableError("Acesso ao BigQuery não autorizado") from exc
        except GoogleAPIError as exc:
            raise BigQueryUnavailableError("Falha ao consultar o BigQuery") from exc
        except Exception as exc:
            raise BigQueryUnavailableError("Integração BigQuery indisponível") from exc

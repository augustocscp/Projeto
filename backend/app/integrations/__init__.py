"""Clientes externos isolados da lógica de negócio da aplicação."""

from app.integrations.bigquery_client import BigQueryClient

__all__ = ["BigQueryClient"]

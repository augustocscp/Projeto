import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/patrimonios"),
        ("get", "/api/patrimonio/resumo"),
        ("get", "/api/categorias-patrimoniais"),
        ("get", "/api/responsaveis"),
        ("get", "/api/integracoes/protheus-bigquery/123"),
    ],
)
def test_rotas_exigem_sessao(method, path):
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        response = getattr(client, method)(path)
    assert response.status_code == 401

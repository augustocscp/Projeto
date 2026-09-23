import os
from collections.abc import Generator

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

TEST_SCHEMA = os.environ.get("DATABASE_SCHEMA", "")
if not TEST_SCHEMA.startswith("gadm_test_"):
    raise RuntimeError("Os testes exigem um DATABASE_SCHEMA temporário iniciado por gadm_test_")

from app.auth import get_current_user  # noqa: E402
from app.config import DATABASE_URL  # noqa: E402
from app.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.categoria_patrimonial import CategoriaPatrimonial  # noqa: E402
from app.models.departamento import Departamento  # noqa: E402
from app.models.empresa import Empresa  # noqa: E402
from app.models.filial import Filial  # noqa: E402
from app.models.localizacao import LocalizacaoVinculo  # noqa: E402
from app.models.responsavel import Responsavel  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Generator[None]:
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")
    try:
        yield
    finally:
        engine.dispose()
        cleanup_engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
        with cleanup_engine.connect() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
        cleanup_engine.dispose()


@pytest.fixture()
def db(migrated_database) -> Generator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def contexto(db: Session) -> dict:
    usuario = Usuario(
        azure_oid="teste-oid",
        nome="Usuário Teste",
        email="teste@example.com",
        cargo="Teste",
        filial="Teste",
        perfil="usuario",
        ativo=True,
    )
    categoria = CategoriaPatrimonial(
        codigo="TESTE",
        nome="Categoria de teste",
        descricao=None,
        ativo=True,
    )
    empresa = db.scalar(select(Empresa).where(Empresa.nome == "Urbi mobilidade"))
    filial = db.scalar(select(Filial).where(Filial.empresa_id == empresa.id))
    vinculo = db.scalar(
        select(LocalizacaoVinculo).where(LocalizacaoVinculo.filial_id == filial.id)
    )
    departamento = db.get(Departamento, vinculo.departamento_id)
    responsavel = Responsavel(
        codigo_re="RE-TESTE",
        nome="Responsável Teste",
        cargo="Teste",
        departamento_id=departamento.id,
        origem_dados="MANUAL",
        ativo=True,
    )
    db.add_all([usuario, categoria, responsavel])
    db.commit()

    def id_dominio(model, codigo: str) -> int:
        return db.scalar(select(model.id).where(model.codigo == codigo))

    from app.models.destinacao_patrimonial import DestinacaoPatrimonial
    from app.models.estado_conservacao import EstadoConservacao
    from app.models.situacao_patrimonial import SituacaoPatrimonial

    payload = {
        "codigo_protheus": None,
        "codigo_sap": None,
        "numero_plaqueta_fisica": "PLAQ-TESTE-001",
        "descricao": "Patrimônio de teste",
        "categoria_id": categoria.id,
        "marca": None,
        "modelo": None,
        "fabricante": None,
        "numero_serie": None,
        "data_fim_garantia": None,
        "empresa_id": empresa.id,
        "filial_id": filial.id,
        "departamento_id": vinculo.departamento_id,
        "localizacao_id": vinculo.localizacao_id,
        "responsavel_id": responsavel.id,
        "estado_conservacao_id": id_dominio(EstadoConservacao, "BOM"),
        "situacao_id": id_dominio(SituacaoPatrimonial, "EM_USO"),
        "destinacao_id": id_dominio(DestinacaoPatrimonial, "USO_INTERNO"),
        "observacao": None,
        "data_baixa": None,
        "numero_patrimonio_anterior": None,
    }
    return {
        "usuario": usuario,
        "categoria": categoria,
        "responsavel": responsavel,
        "payload": payload,
    }


@pytest.fixture()
def client(db: Session, contexto):
    from fastapi.testclient import TestClient

    def override_db():
        yield db

    def override_user():
        usuario = contexto["usuario"]
        return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email}

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

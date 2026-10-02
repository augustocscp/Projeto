import os
import re
from collections.abc import Generator
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

ORIGINAL_DATABASE_SCHEMA = os.environ.get("DATABASE_SCHEMA", "gadm")
GENERATED_TEST_SCHEMA = f"gadm_test_{uuid4().hex}"
os.environ["DATABASE_SCHEMA"] = GENERATED_TEST_SCHEMA
os.environ["GCP_BIGQUERY_ENABLED"] = "false"
TEST_SCHEMA = os.environ.get("DATABASE_SCHEMA", "")
if not TEST_SCHEMA.startswith("gadm_test_"):
    raise RuntimeError("Os testes exigem um DATABASE_SCHEMA temporário iniciado por gadm_test_")

from app.auth import get_current_user  # noqa: E402
from app.config import DATABASE_URL, validate_database_schema  # noqa: E402
from app.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.categoria_patrimonial import CategoriaPatrimonial  # noqa: E402
from app.models.departamento import Departamento  # noqa: E402
from app.models.empresa import Empresa  # noqa: E402
from app.models.filial import Filial  # noqa: E402
from app.models.localizacao import LocalizacaoVinculo  # noqa: E402
from app.models.responsavel import Responsavel  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

TEST_SCHEMA = validate_database_schema(TEST_SCHEMA)
_SCHEMA_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,62}")
MANIFEST_SCHEMAS = tuple(
    sorted(
        {
            "public",
            *(
                (ORIGINAL_DATABASE_SCHEMA,)
                if _SCHEMA_PATTERN.fullmatch(ORIGINAL_DATABASE_SCHEMA)
                else ()
            ),
        }
    )
)


def _schema_identity(connection, schema: str) -> tuple[int, int] | None:
    namespaces = sa.table(
        "pg_namespace",
        sa.column("oid", sa.Integer()),
        sa.column("nspname", sa.String()),
        sa.column("nspowner", sa.Integer()),
        schema="pg_catalog",
    )
    row = connection.execute(
        sa.select(namespaces.c.oid, namespaces.c.nspowner).where(
            namespaces.c.nspname == schema
        )
    ).one_or_none()
    return tuple(row) if row is not None else None


def _schema_manifest(connection, schema: str) -> dict:
    inspector = inspect(connection)
    if not inspector.has_schema(schema):
        return {"exists": False}

    tables = sorted(inspector.get_table_names(schema=schema))
    table_details = {}
    for table in tables:
        table_details[table] = {
            "columns": [
                (column["name"], str(column["type"]), column["nullable"])
                for column in inspector.get_columns(table, schema=schema)
            ],
            "indexes": sorted(
                (
                    index["name"],
                    tuple(index.get("column_names") or ()),
                    bool(index.get("unique")),
                )
                for index in inspector.get_indexes(table, schema=schema)
            ),
            "foreign_keys": sorted(
                (
                    key.get("name"),
                    tuple(key.get("constrained_columns") or ()),
                    key.get("referred_schema"),
                    key.get("referred_table"),
                    tuple(key.get("referred_columns") or ()),
                )
                for key in inspector.get_foreign_keys(table, schema=schema)
            ),
            "unique_constraints": sorted(
                (
                    constraint.get("name"),
                    tuple(constraint.get("column_names") or ()),
                )
                for constraint in inspector.get_unique_constraints(
                    table, schema=schema
                )
            ),
            "check_constraints": sorted(
                (
                    constraint.get("name"),
                    constraint.get("sqltext"),
                )
                for constraint in inspector.get_check_constraints(
                    table, schema=schema
                )
            ),
        }

    namespaces = sa.table(
        "pg_namespace",
        sa.column("oid", sa.Integer()),
        sa.column("nspname", sa.String()),
        schema="pg_catalog",
    )
    classes = sa.table(
        "pg_class",
        sa.column("oid", sa.Integer()),
        sa.column("relnamespace", sa.Integer()),
        sa.column("relname", sa.String()),
        schema="pg_catalog",
    )
    procedures = sa.table(
        "pg_proc",
        sa.column("pronamespace", sa.Integer()),
        sa.column("proname", sa.String()),
        sa.column("prokind", sa.String()),
        schema="pg_catalog",
    )
    triggers = sa.table(
        "pg_trigger",
        sa.column("tgrelid", sa.Integer()),
        sa.column("tgname", sa.String()),
        sa.column("tgisinternal", sa.Boolean()),
        schema="pg_catalog",
    )
    types = sa.table(
        "pg_type",
        sa.column("typnamespace", sa.Integer()),
        sa.column("typname", sa.String()),
        sa.column("typtype", sa.String()),
        schema="pg_catalog",
    )
    namespace_id = sa.select(namespaces.c.oid).where(
        namespaces.c.nspname == schema
    ).scalar_subquery()
    return {
        "exists": True,
        "tables": table_details,
        "views": sorted(inspector.get_view_names(schema=schema)),
        "sequences": sorted(inspector.get_sequence_names(schema=schema)),
        "functions": sorted(
            connection.execute(
                sa.select(procedures.c.proname, procedures.c.prokind).where(
                    procedures.c.pronamespace == namespace_id
                )
            ).tuples()
        ),
        "triggers": sorted(
            connection.execute(
                sa.select(classes.c.relname, triggers.c.tgname)
                .join(classes, classes.c.oid == triggers.c.tgrelid)
                .where(
                    classes.c.relnamespace == namespace_id,
                    triggers.c.tgisinternal.is_(False),
                )
            ).tuples()
        ),
        "types": sorted(
            connection.execute(
                sa.select(types.c.typname, types.c.typtype).where(
                    types.c.typnamespace == namespace_id
                )
            ).tuples()
        ),
    }


def _database_manifest(connection) -> dict:
    extensions = sa.table(
        "pg_extension",
        sa.column("extname", sa.String()),
        sa.column("extversion", sa.String()),
        schema="pg_catalog",
    )
    return {
        "schemas": {
            schema: _schema_manifest(connection, schema)
            for schema in MANIFEST_SCHEMAS
        },
        "extensions": sorted(
            connection.execute(
                sa.select(extensions.c.extname, extensions.c.extversion)
            ).tuples()
        ),
    }


def _load_migration_0002():
    migration_path = (
            Path(__file__).resolve().parents[1]
            / "alembic"
            / "versions"
            / "0002_cria_estrutura_organizacional_e_localizacoes.py"
    )
    spec = spec_from_file_location("migration_0002_security_test", migration_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Nao foi possivel carregar a migration 0002")
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


@pytest.fixture(scope="session")
def migrated_database() -> Generator[None]:
    ownership_engine = create_engine(DATABASE_URL)
    schema_owned = False
    schema_identity = None
    manifest_before = None
    primary_error = None
    with ownership_engine.begin() as connection:
        manifest_before = _database_manifest(connection)
        if inspect(connection).has_schema(TEST_SCHEMA):
            raise RuntimeError("O schema temporario gerado ja existe")
        connection.execute(CreateSchema(TEST_SCHEMA))
        schema_identity = _schema_identity(connection, TEST_SCHEMA)
        if schema_identity is None:
            raise RuntimeError("Nao foi possivel confirmar a criacao do schema temporario")
    schema_owned = True

    alembic_config = Config("alembic.ini")
    try:
        command.upgrade(alembic_config, "0002")
        migration_0002 = _load_migration_0002()
        with engine.begin() as connection:
            migration_0002._seed_localizacao_vinculos(connection)
            migration_0002._seed_localizacao_vinculos(connection)
        command.upgrade(alembic_config, "0006")
        command.downgrade(alembic_config, "0005")
        command.upgrade(alembic_config, "0015")
        command.downgrade(alembic_config, "0014")
        command.upgrade(alembic_config, "0016")
        command.downgrade(alembic_config, "0015")
        command.upgrade(alembic_config, "0017")
        command.downgrade(alembic_config, "0016")
        command.upgrade(alembic_config, "0018")
        command.downgrade(alembic_config, "0017")
        command.upgrade(alembic_config, "head")
        command.upgrade(alembic_config, "head")
        yield
    except BaseException as exc:
        primary_error = exc
    finally:
        engine.dispose()
        ownership_engine.dispose()
        cleanup_error = None
        if (
                schema_owned
                and TEST_SCHEMA == GENERATED_TEST_SCHEMA
                and validate_database_schema(TEST_SCHEMA) == TEST_SCHEMA
                and TEST_SCHEMA.startswith("gadm_test_")
        ):
            cleanup_engine = create_engine(DATABASE_URL)
            try:
                with cleanup_engine.begin() as connection:
                    if _schema_identity(connection, TEST_SCHEMA) != schema_identity:
                        raise RuntimeError(
                            "A propriedade do schema temporario mudou; limpeza recusada"
                        )
                    connection.execute(
                        DropSchema(TEST_SCHEMA, cascade=True, if_exists=True)
                    )
                    manifest_after = _database_manifest(connection)
                    if manifest_after != manifest_before:
                        raise RuntimeError(
                            "Objetos preexistentes foram alterados durante os testes"
                        )
            except BaseException as exc:
                cleanup_error = exc
            finally:
                cleanup_engine.dispose()

        if primary_error is not None and cleanup_error is not None:
            raise BaseExceptionGroup(
                "Falha nos testes e na limpeza do schema temporario",
                [primary_error, cleanup_error],
            )
        if primary_error is not None:
            raise primary_error.with_traceback(primary_error.__traceback__)
        if cleanup_error is not None:
            raise cleanup_error.with_traceback(cleanup_error.__traceback__)


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
        nome="Categoria de teste",
        ativo=True,
    )
    empresa = db.scalar(select(Empresa).where(Empresa.nome == "Urbi mobilidade"))
    filial = db.scalar(select(Filial).where(Filial.empresa_id == empresa.id))
    vinculo = db.scalar(
        select(LocalizacaoVinculo).where(LocalizacaoVinculo.filial_id == filial.id)
    )
    departamento = db.get(Departamento, vinculo.departamento_id)
    responsavel = Responsavel(
        codigo_re="00123",
        nome="Responsável Teste",
        cargo="Teste",
        departamento_id=departamento.id,
        origem_dados="MANUAL",
        ativo=True,
    )
    db.add_all([usuario, categoria, responsavel])
    db.commit()

    def id_dominio(model, valor: str, campo: str = "codigo") -> int:
        return db.scalar(select(model.id).where(getattr(model, campo) == valor))

    from app.models.destinacao_patrimonial import DestinacaoPatrimonial
    from app.models.estado_conservacao import EstadoConservacao
    from app.models.situacao_patrimonial import SituacaoPatrimonial

    payload = {
        "codigo_protheus": "0000006003",
        "numero_item": "0001",
        "codigo_sap": None,
        "numero_plaqueta_fisica": "PLAQ000001",
        "descricao": "Patrimônio de teste",
        "categoria_id": categoria.id,
        "marca": None,
        "modelo": None,
        "fabricante": None,
        "numero_serie": "SERIE-TESTE",
        "possui_garantia": False,
        "data_fim_garantia": None,
        "empresa_id": empresa.id,
        "filial_id": filial.id,
        "departamento_id": vinculo.departamento_id,
        "localizacao_id": vinculo.localizacao_id,
        "codigo_re": responsavel.codigo_re,
        "estado_conservacao_id": id_dominio(EstadoConservacao, "BOM"),
        "situacao_id": id_dominio(SituacaoPatrimonial, "EM_USO"),
        "destinacao_id": id_dominio(
            DestinacaoPatrimonial, "Operacional", campo="nome"
        ),
        "observacao": None,
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

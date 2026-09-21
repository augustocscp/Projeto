from collections.abc import Generator

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_SCHEMA, DATABASE_URL


class Base(DeclarativeBase):
    metadata = MetaData(schema=DATABASE_SCHEMA)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database_objects() -> None:
    import app.models.sessao  # noqa: F401
    import app.models.usuario  # noqa: F401

    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DATABASE_SCHEMA}"'))

    Base.metadata.create_all(bind=engine)

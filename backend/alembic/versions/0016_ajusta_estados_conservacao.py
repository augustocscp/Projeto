"""ajusta estados de conservacao para novos cadastros

Revision ID: 0016
Revises: 0015
"""

from alembic import op
import sqlalchemy as sa

from app.config import DATABASE_SCHEMA

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def _aplicar_estados(estados: tuple[tuple[str, str], ...]) -> None:
    bind = op.get_bind()
    for ordem, (codigo, nome) in enumerate(estados, start=1):
        bind.execute(
            sa.text(
                f"""
                INSERT INTO {DATABASE_SCHEMA}.estados_conservacao (
                    codigo,
                    nome,
                    descricao,
                    ativo,
                    ordem_exibicao
                )
                VALUES (:codigo, :nome, NULL, true, :ordem)
                ON CONFLICT (codigo) DO UPDATE
                SET nome = EXCLUDED.nome,
                    ativo = true,
                    ordem_exibicao = EXCLUDED.ordem_exibicao,
                    atualizado_em = now()
                """
            ),
            {"codigo": codigo, "nome": nome, "ordem": ordem},
        )

    codigos = tuple(codigo for codigo, _ in estados)
    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.estados_conservacao
            SET ativo = false,
                atualizado_em = now()
            WHERE codigo NOT IN :codigos
            """
        ).bindparams(sa.bindparam("codigos", expanding=True)),
        {"codigos": codigos},
    )


def upgrade() -> None:
    _aplicar_estados(
        (
            ("OTIMO", "Ótimo"),
            ("BOM", "Bom"),
            ("REGULAR", "Regular"),
            ("RUIM", "Ruim"),
            ("DANIFICADO", "Danificado"),
            ("NAO_AVALIADO", "Não avaliado"),
        )
    )


def downgrade() -> None:
    _aplicar_estados(
        (
            ("NOVO", "Novo"),
            ("OTIMO", "Ótimo"),
            ("BOM", "Bom"),
            ("REGULAR", "Regular"),
            ("RUIM", "Ruim"),
            ("INSERVIVEL", "Inservível"),
        )
    )

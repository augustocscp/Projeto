"""ajusta destinacoes patrimoniais

Revision ID: 0017
Revises: 0016
"""

from alembic import op
import sqlalchemy as sa

from app.config import DATABASE_SCHEMA

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.destinacoes_patrimoniais
            SET codigo = 'OPERACIONAL',
                nome = 'Operacional',
                ativo = true,
                atualizado_em = now()
            WHERE codigo = 'OPERACAO'
            """
        )
    )
    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.destinacoes_patrimoniais
            SET codigo = 'ADMINISTRATIVO',
                nome = 'Administrativo',
                ativo = true,
                atualizado_em = now()
            WHERE codigo = 'ADMINISTRACAO'
            """
        )
    )
    bind.execute(
        sa.text(
            f"""
            INSERT INTO {DATABASE_SCHEMA}.destinacoes_patrimoniais (
                codigo,
                nome,
                descricao,
                ativo,
                ordem_exibicao
            )
            SELECT
                'DOACAO',
                'Doação',
                NULL,
                true,
                COALESCE(MAX(ordem_exibicao), 0) + 1
            FROM {DATABASE_SCHEMA}.destinacoes_patrimoniais
            ON CONFLICT (codigo) DO UPDATE
            SET nome = EXCLUDED.nome,
                ativo = true,
                atualizado_em = now()
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.destinacoes_patrimoniais
            SET codigo = 'OPERACAO',
                nome = 'Operação',
                atualizado_em = now()
            WHERE codigo = 'OPERACIONAL'
            """
        )
    )
    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.destinacoes_patrimoniais
            SET codigo = 'ADMINISTRACAO',
                nome = 'Administração',
                atualizado_em = now()
            WHERE codigo = 'ADMINISTRATIVO'
            """
        )
    )
    bind.execute(
        sa.text(
            f"""
            DELETE FROM {DATABASE_SCHEMA}.destinacoes_patrimoniais d
            WHERE d.codigo = 'DOACAO'
              AND NOT EXISTS (
                  SELECT 1
                  FROM {DATABASE_SCHEMA}.patrimonios p
                  WHERE p.destinacao_id = d.id
              )
            """
        )
    )
    bind.execute(
        sa.text(
            f"""
            UPDATE {DATABASE_SCHEMA}.destinacoes_patrimoniais
            SET ativo = false,
                atualizado_em = now()
            WHERE codigo = 'DOACAO'
            """
        )
    )

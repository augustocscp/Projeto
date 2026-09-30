"""move coordenacao para o escritorio matriz

Revision ID: 0015
Revises: 0014
"""

from alembic import op

from app.config import DATABASE_SCHEMA

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def _mover_vinculos(nome_filial_destino: str, manter_departamento: str) -> None:
    op.execute(
        f"""
        WITH filial_destino AS (
            SELECT filial.id
            FROM {DATABASE_SCHEMA}.filiais AS filial
            JOIN {DATABASE_SCHEMA}.empresas AS empresa
              ON empresa.id = filial.empresa_id
            WHERE empresa.nome ILIKE 'Urbi mobilidade'
              AND filial.nome ILIKE '%{nome_filial_destino}%'
            LIMIT 1
        ),
        vinculos_destino AS (
            SELECT
                vinculo.localizacao_id,
                filial_destino.id AS filial_id,
                vinculo.departamento_id,
                bool_or(vinculo.ativo) AS ativo,
                min(vinculo.criado_em) AS criado_em
            FROM {DATABASE_SCHEMA}.localizacao_vinculos AS vinculo
            JOIN {DATABASE_SCHEMA}.localizacoes AS localizacao
              ON localizacao.id = vinculo.localizacao_id
            JOIN {DATABASE_SCHEMA}.departamentos AS departamento
              ON departamento.id = vinculo.departamento_id
            CROSS JOIN filial_destino
            WHERE localizacao.nome ILIKE 'COORDENA%'
              AND departamento.codigo <> '{manter_departamento}'
            GROUP BY
                vinculo.localizacao_id,
                filial_destino.id,
                vinculo.departamento_id
        )
        INSERT INTO {DATABASE_SCHEMA}.localizacao_vinculos (
            localizacao_id,
            filial_id,
            departamento_id,
            ativo,
            criado_em,
            atualizado_em
        )
        SELECT
            localizacao_id,
            filial_id,
            departamento_id,
            ativo,
            criado_em,
            now()
        FROM vinculos_destino
        ON CONFLICT (localizacao_id, filial_id, departamento_id) DO UPDATE
        SET ativo = EXCLUDED.ativo,
            atualizado_em = now();

        WITH filial_destino AS (
            SELECT filial.id
            FROM {DATABASE_SCHEMA}.filiais AS filial
            JOIN {DATABASE_SCHEMA}.empresas AS empresa
              ON empresa.id = filial.empresa_id
            WHERE empresa.nome ILIKE 'Urbi mobilidade'
              AND filial.nome ILIKE '%{nome_filial_destino}%'
            LIMIT 1
        )
        UPDATE {DATABASE_SCHEMA}.patrimonios AS patrimonio
        SET filial_id = filial_destino.id,
            data_ultima_atualizacao = now()
        FROM {DATABASE_SCHEMA}.localizacoes AS localizacao,
             filial_destino
        WHERE patrimonio.localizacao_id = localizacao.id
          AND localizacao.nome ILIKE 'COORDENA%'
          AND patrimonio.filial_id <> filial_destino.id
          AND EXISTS (
              SELECT 1
              FROM {DATABASE_SCHEMA}.departamentos AS departamento
              WHERE departamento.id = patrimonio.departamento_id
                AND departamento.codigo <> '{manter_departamento}'
          );

        WITH filial_destino AS (
            SELECT filial.id
            FROM {DATABASE_SCHEMA}.filiais AS filial
            JOIN {DATABASE_SCHEMA}.empresas AS empresa
              ON empresa.id = filial.empresa_id
            WHERE empresa.nome ILIKE 'Urbi mobilidade'
              AND filial.nome ILIKE '%{nome_filial_destino}%'
            LIMIT 1
        )
        DELETE FROM {DATABASE_SCHEMA}.localizacao_vinculos AS vinculo
        USING {DATABASE_SCHEMA}.localizacoes AS localizacao,
              {DATABASE_SCHEMA}.departamentos AS departamento,
              filial_destino
        WHERE vinculo.localizacao_id = localizacao.id
          AND vinculo.departamento_id = departamento.id
          AND localizacao.nome ILIKE 'COORDENA%'
          AND vinculo.filial_id <> filial_destino.id
          AND departamento.codigo <> '{manter_departamento}';
        """
    )


def upgrade() -> None:
    _mover_vinculos("matriz", "")


def downgrade() -> None:
    _mover_vinculos("Samambaia", "GSMA")

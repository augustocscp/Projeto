"""cria estrutura organizacional e localizacoes

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.schema import CreateSchema

from app.config import DATABASE_SCHEMA

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

LOCALIZACAO_VINCULOS = (
    ("TERMINAL RIACHO FUNDO I", "Terminal", "GOPE"),
    ("SALA TAMBOR FREIO", "Garagem Recanto", "GSMA"),
    ("SIAT", "Garagem Recanto", "GOPE"),
    ("RECEPCAO", "Escritorio Executivo", "DCOL"),
    ("SALA EXECUTIVA", "Escritorio Executivo", "DCOL"),
    ("COPA", "Escritorio Executivo", "DCOL"),
    ("SALA REUNIAO", "Escritorio Executivo", "DCOL"),
    ("SALA LABORATORIO TINTA", "Garagem Recanto", "GPVE"),
    ("SALA TAMBOR FREIO", "Garagem Samambaia", "GSMA"),
    ("SALA SUCATA TAMBOR", "Garagem Samambaia", "GSMA"),
    ("SALA RESIDUO PNEU", "Garagem Samambaia", "GSMA"),
    ("SALA RECICLAGEM SUCATA", "Garagem Recanto", "GSMA"),
    ("SALA REBITACAO LONA", "Garagem Samambaia", "GPVE"),
    ("CALIBRAGEM PNEU", "Garagem Samambaia", "GPVE"),
    ("SALA OLEO", "Garagem Samambaia", "GSMA"),
    ("SALA MONTAGEM", "Garagem Recanto", "GPVE"),
    ("SALA LAVADOR PECA", "Garagem Recanto", "GPVE"),
    ("SALA LANTERNAGEM", "Garagem Recanto", "GPVE"),
    ("SALA FERRAMENTARIA", "Garagem Recanto", "GPVE"),
    ("SALA ELETRICA", "Garagem Recanto", "GPVE"),
    ("SALA DESCANSO LAVADOR", "Garagem Recanto", "GPVE"),
    ("SALA COMPRESSOR", "Garagem Recanto", "GPVE"),
    ("SALA BORRACHARIA", "Garagem Recanto", "GPVE"),
    ("SALA ASSISTENCIA TECNICA", "Garagem Recanto", "GPVE"),
    ("PATIO ONIBUS", "Garagem Recanto", "GPVE"),
    ("PATIO MANUTENCAO", "Garagem Recanto", "GPVE"),
    ("LAVADOR MANUAL", "Garagem Recanto", "GPVE"),
    ("ESCOVA", "Garagem Recanto", "GPVE"),
    ("ABASTECIMENTO", "Garagem Recanto", "GPVE"),
    ("VESTIARIO MASCULINO", "Garagem Recanto", "GPVE"),
    ("SUPERVISAO", "Garagem Recanto", "GOPE"),
    ("SALA IV ENFERMEIRA", "Garagem Samambaia", "GSMA"),
    ("SALA INFRAESTRUTURA", "Garagem Recanto", "GADM"),
    ("REFEITORIO", "Garagem Recanto", "GADM"),
    ("GUARITA AGP", "Garagem Samambaia", "GADM"),
    ("COPA", "Garagem Recanto", "GADM"),
    ("RECEBIMENTO NOTA", "Garagem Recanto", "GDEN"),
    ("SALA SEGURANCA TRABALHO", "Garagem Recanto", "GSMA"),
    ("SALA REUNIAO EMPREENDEDORISMO", "Garagem Recanto", "G&C"),
    ("SALA OLEO", "Garagem Recanto", "GSMA"),
    ("SALA ALMOXARIFADO", "Garagem Recanto", "GSUP"),
    ("CPD I  (ANTIGO)", "Garagem Recanto", "GTSI"),
    ("SIAT", "Garagem Samambaia", "GOPE"),
    ("SALA DIRETORIA TRANSPORTE", "Escritorio matriz", "DCOL"),
    ("SALA DA GERENCIA", "Escritorio matriz", "GTRA"),
    ("SALA DA GERENCIA", "Escritorio matriz", "GPSN"),
    ("SALA DA GERENCIA", "Escritorio matriz", "GPVE"),
    ("VESTIARIO MASCULINO", "Garagem Samambaia", "GPVE"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GPQS"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GOPE"),
    ("SALA CFTV", "Escritorio matriz", "GOPE"),
    ("SALA CCO", "Escritorio matriz", "GOPE"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GMKT"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GADM"),
    ("SALA PATRIMONIO", "Garagem Samambaia", "GADM"),
    ("SALA INFRAESTRUTURA", "Garagem Samambaia", "GADM"),
    ("REFEITORIO", "Garagem Samambaia", "GADM"),
    ("RECEPCAO", "Garagem Samambaia", "GADM"),
    ("SALA LEITURA", "Escritorio matriz", "GADM"),
    ("ESPACO HAILE PINHEIRO", "Garagem Samambaia", "G&C"),
    ("COPA ADM I (SALAO ADMINISTRATIVO)", "Garagem Samambaia", "GADM"),
    ("VESTIARIO FEMININO", "Garagem Samambaia", "GADM"),
    ("ARQUIVO", "Garagem Samambaia", "GADM"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GRC"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GDEN"),
    ("RECEBIMENTO NOTA", "Garagem Samambaia", "GDEN"),
    ("COORDENAÇÃO", "Garagem Samambaia", "G&C"),
    ("SALA III MEDICO", "Escritorio matriz", "GSMA"),
    ("SALA II PSICOLOGO", "Escritorio matriz", "GSMA"),
    ("SALA RESIDUO CONTAMINADO", "Escritorio matriz", "GSMA"),
    ("DEPOSITO", "Garagem Samambaia", "G&C"),
    ("SALA RESIDUO CONTAMINADO", "Garagem Recanto", "GSMA"),
    ("SALA I MEDICO", "Escritorio matriz", "GSMA"),
    ("SALA CENTRAL DE RESIDUO", "Garagem Samambaia", "GSMA"),
    ("ATENDIMENTO", "Garagem Samambaia", "GSMA"),
    ("SALA EXTINTOR", "Garagem Samambaia", "GSMA"),
    ("SALA DE ESPERA", "Garagem Samambaia", "G&C"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GIPE"),
    ("ONIBUS TREINAMENTO", "Garagem Samambaia", "G&C"),
    ("COORDENAÇÃO", "Garagem Samambaia", "DP"),
    ("SALA SEPARACAO", "Garagem Samambaia", "GSMA"),
    ("SALA REUNIAO RESULTADO", "Garagem Samambaia", "GADM"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GSOR"),
    ("SATO III", "Escritorio matriz", "GSOR"),
    ("SATO II", "Escritorio matriz", "GSOR"),
    ("SATO I", "Escritorio matriz", "GSOR"),
    ("SATO IV", "Escritorio matriz", "GSOR"),
    ("CORREDOR SATO", "Escritorio matriz", "GSOR"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GSUP"),
    ("ALMOXARIFADO MECANICA", "Garagem Samambaia", "GSUP"),
    ("ALMOXARIFADO ADM", "Garagem Samambaia", "GSUP"),
    ("CPD", "Garagem Samambaia", "GTSI"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GTSI"),
    ("COORDENAÇÃO", "Garagem Samambaia", "GPVE"),
    ("SALA REBITACAO LONA", "Garagem Recanto", "GPVE"),
    ("SALA PRODUTO QUIMICO", "Garagem Samambaia", "GPVE"),
    ("SALA DE PROVA", "Garagem Samambaia", "G&C"),
    ("SALA ELETRICA", "Garagem Samambaia", "GPVE"),
    ("SALA MONTAGEM CUBO", "Garagem Samambaia", "GPVE"),
    ("SALA LAVAGEM PECA", "Garagem Samambaia", "GPVE"),
    ("SALA LANTERNAGEM", "Garagem Samambaia", "GPVE"),
    ("SALA FERRAMENTARIA MECANICA", "Garagem Samambaia", "GPVE"),
    ("SALA CUBO", "Garagem Samambaia", "GPVE"),
    ("SALA BORRACHARIA", "Garagem Samambaia", "GPVE"),
    ("SALA ASSISTENCIA TECNICA", "Garagem Samambaia", "GPVE"),
    ("PATIO ONIBUS", "Garagem Samambaia", "GPVE"),
    ("PATIO MANUTENCAO", "Garagem Samambaia", "GPVE"),
    ("LAVADOR MANUAL SAM I", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO I", "Garagem Samambaia", "GPVE"),
    ("SALA RECARGA BATERIA", "Garagem Samambaia", "GPVE"),
    ("TERMINAL AGUA QUENTE", "Terminal", "GOPE"),
    ("TERMINAL CAUB II", "Terminal", "GOPE"),
    ("TERMINAL SALA RODOVIARIA", "Terminal", "GOPE"),
    ("TERMINAL UNICEUB", "Terminal", "GOPE"),
    ("TERMINAL NUCLEO BANDEIRANTE", "Terminal", "GOPE"),
    ("TERMINAL RECANTO 143", "Terminal", "GOPE"),
    ("TERMINAL RECANTO 251", "Terminal", "GOPE"),
    ("SALA SINISTRO", "Escritorio matriz", "GSOR"),
    ("TERMINAL SANTA HELENA", "Terminal", "GOPE"),
    ("TERMINAL SETOR O", "Terminal", "GOPE"),
    ("SALA ACHADOS E PERDIDOS", "Escritorio matriz", "GSOR"),
    ("PORTAO ACESSO LADO BR", "Garagem Samambaia", "GADM"),
    ("PORTAO ACESSO", "Garagem Samambaia", "GADM"),
    ("PORTAO ACESSO INTERNO", "Garagem Recanto", "GADM"),
    ("CPD II (NOVO)", "Garagem Recanto", "GTSI"),
    ("TERMINAL SAM NORTE", "Terminal", "GOPE"),
    ("TERMINAL SAM SUL", "Terminal", "GOPE"),
    ("ESTACIONAMENTO INTERNO", "Garagem Samambaia", "GADM"),
    ("ESTACIONAMENTO EXTERNO", "Garagem Samambaia", "GADM"),
    ("PORTAO ACESSO EXTERNO", "Garagem Recanto", "GADM"),
    ("MURO", "Garagem Recanto", "GADM"),
    ("MURO", "Garagem Samambaia", "GADM"),
    ("VALA GALPAO NOVO", "Garagem Recanto", "GPVE"),
    ("PORTARIA PEDESTRE", "Garagem Recanto", "GADM"),
    ("CAIXA LAVADOR II", "Garagem Recanto", "GPVE"),
    ("CAIXA LAVADOR I", "Garagem Recanto", "GPVE"),
    ("SALA LUBRIFICANTE", "Garagem Samambaia", "GPVE"),
    ("SALA LANCHE GPVE", "Garagem Samambaia", "GADM"),
    ("TANQUE LAVADOR MANUAL", "Garagem Samambaia", "GPVE"),
    ("SALA BOMBA MANUAL", "Garagem Samambaia", "GPVE"),
    ("SALA COMPRESSOR", "Garagem Samambaia", "GPVE"),
    ("BANHEIRO MASCULINO ADM", "Escritorio matriz", "GADM"),
    ("BANHEIRO FEMININO ADM", "Escritorio matriz", "GADM"),
    ("BANHEIRO MASCULINO ADM", "Garagem Recanto", "GADM"),
    ("BANHEIRO FEMININO ADM", "Garagem Recanto", "GADM"),
    ("BANHEIRO MASCULINO", "Garagem Recanto", "GPVE"),
    ("BANHEIRO MASCULINO", "Garagem Recanto", "GSUP"),
    ("BOX OFICINA I", "Garagem Samambaia", "GPVE"),
    ("BOX OFICINA II", "Garagem Samambaia", "GPVE"),
    ("BOX OFICINA III", "Garagem Samambaia", "GPVE"),
    ("BOX OFICINA IV", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO II", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO III", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO IV", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO V", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO VI", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO VII", "Garagem Samambaia", "GPVE"),
    ("ABASTECIMENTO VIII", "Garagem Samambaia", "GPVE"),
    ("CAIXA GERADOR", "Garagem Recanto", "GADM"),
    ("SALA REUNIAO AMOR EM SERVIR", "Garagem Samambaia", "GADM"),
    ("SALA RESERVA PATRIMONIO", "Garagem Samambaia", "GADM"),
    ("COPA ADM II (CAFÉ)", "Garagem Samambaia", "GADM"),
    ("SALA ARMARIOS", "Garagem Samambaia", "GADM"),
    ("GALPAO ANTIGO", "Garagem Recanto", "GPVE"),
    ("SALA ASSISTENCIA TECNICA GALPAO NOVO", "Garagem Recanto", "GPVE"),
    ("INFRAESTRUTURA", "Garagem Samambaia", "GADM"),
    ("INFRAESTRUTURA", "Garagem Recanto", "GADM"),
    ("COMODATO", "Garagem Samambaia", "GADM"),
    ("SALA REUNIAO RH", "Escritorio matriz", "G&C"),
    ("SALA REUNIAO INOVACAO", "Escritorio matriz", "GADM"),
    ("SALA DEPOSITO", "Garagem Samambaia", "GMKT"),
    ("COORDENAÇÃO", "Escritorio matriz", "GSMA"),
)


def upgrade() -> None:
    op.execute(CreateSchema(DATABASE_SCHEMA, if_not_exists=True))

    op.create_table(
        "empresas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("cnpj", sa.String(length=20), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("nome", name="uq_empresas_nome"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_empresas_id", "empresas", ["id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_empresas_nome", "empresas", ["nome"], schema=DATABASE_SCHEMA)

    op.create_table(
        "cidades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("codigo_ibge", sa.String(length=20), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("nome", "uf", name="uq_cidades_nome_uf"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_cidades_id", "cidades", ["id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_cidades_nome", "cidades", ["nome"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_cidades_uf", "cidades", ["uf"], schema=DATABASE_SCHEMA)

    op.create_table(
        "filiais",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cidade_id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo_unidade", sa.String(length=20), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "tipo_unidade IN ('TERMINAL', 'GARAGEM', 'ESCRITORIO')",
            name="ck_filiais_tipo_unidade",
        ),
        sa.ForeignKeyConstraint(["cidade_id"], [f"{DATABASE_SCHEMA}.cidades.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], [f"{DATABASE_SCHEMA}.empresas.id"]),
        sa.UniqueConstraint("empresa_id", "nome", name="uq_filiais_empresa_nome"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_filiais_id", "filiais", ["id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_filiais_empresa_id", "filiais", ["empresa_id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_filiais_cidade_id", "filiais", ["cidade_id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_filiais_nome", "filiais", ["nome"], schema=DATABASE_SCHEMA)

    op.create_table(
        "departamentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("codigo", name="uq_departamentos_codigo"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_departamentos_id", "departamentos", ["id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_departamentos_codigo", "departamentos", ["codigo"], schema=DATABASE_SCHEMA)

    op.create_table(
        "localizacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), nullable=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "tipo IN ("
            "'SALA', 'BAIA', 'PATIO', 'TERMINAL', 'PORTAO', "
            "'BANHEIRO', 'ESTACIONAMENTO', 'DEPOSITO', "
            "'AREA_OPERACIONAL', 'OUTRO'"
            ")",
            name="ck_localizacoes_tipo",
        ),
        sa.UniqueConstraint("nome", name="uq_localizacoes_nome"),
        schema=DATABASE_SCHEMA,
    )
    op.create_index("ix_gadm_localizacoes_id", "localizacoes", ["id"], schema=DATABASE_SCHEMA)
    op.create_index("ix_gadm_localizacoes_nome", "localizacoes", ["nome"], schema=DATABASE_SCHEMA)

    op.create_table(
        "localizacao_vinculos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("localizacao_id", sa.Integer(), nullable=False),
        sa.Column("filial_id", sa.Integer(), nullable=False),
        sa.Column("departamento_id", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["localizacao_id"], [f"{DATABASE_SCHEMA}.localizacoes.id"]),
        sa.ForeignKeyConstraint(["filial_id"], [f"{DATABASE_SCHEMA}.filiais.id"]),
        sa.ForeignKeyConstraint(["departamento_id"], [f"{DATABASE_SCHEMA}.departamentos.id"]),
        sa.UniqueConstraint(
            "localizacao_id",
            "filial_id",
            "departamento_id",
            name="uq_localizacao_vinculos_localizacao_filial_departamento",
        ),
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_id",
        "localizacao_vinculos",
        ["id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_localizacao_id",
        "localizacao_vinculos",
        ["localizacao_id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_filial_id",
        "localizacao_vinculos",
        ["filial_id"],
        schema=DATABASE_SCHEMA,
    )
    op.create_index(
        "ix_gadm_localizacao_vinculos_departamento_id",
        "localizacao_vinculos",
        ["departamento_id"],
        schema=DATABASE_SCHEMA,
    )

    _seed_initial_data()


def downgrade() -> None:
    op.drop_index(
        "ix_gadm_localizacao_vinculos_departamento_id",
        table_name="localizacao_vinculos",
        schema=DATABASE_SCHEMA,
    )
    op.drop_index(
        "ix_gadm_localizacao_vinculos_filial_id",
        table_name="localizacao_vinculos",
        schema=DATABASE_SCHEMA,
    )
    op.drop_index(
        "ix_gadm_localizacao_vinculos_localizacao_id",
        table_name="localizacao_vinculos",
        schema=DATABASE_SCHEMA,
    )
    op.drop_index(
        "ix_gadm_localizacao_vinculos_id",
        table_name="localizacao_vinculos",
        schema=DATABASE_SCHEMA,
    )
    op.drop_table("localizacao_vinculos", schema=DATABASE_SCHEMA)

    op.drop_index("ix_gadm_localizacoes_nome", table_name="localizacoes", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_localizacoes_id", table_name="localizacoes", schema=DATABASE_SCHEMA)
    op.drop_table("localizacoes", schema=DATABASE_SCHEMA)

    op.drop_index("ix_gadm_departamentos_codigo", table_name="departamentos", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_departamentos_id", table_name="departamentos", schema=DATABASE_SCHEMA)
    op.drop_table("departamentos", schema=DATABASE_SCHEMA)

    op.drop_index("ix_gadm_filiais_nome", table_name="filiais", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_filiais_cidade_id", table_name="filiais", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_filiais_empresa_id", table_name="filiais", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_filiais_id", table_name="filiais", schema=DATABASE_SCHEMA)
    op.drop_table("filiais", schema=DATABASE_SCHEMA)

    op.drop_index("ix_gadm_cidades_uf", table_name="cidades", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_cidades_nome", table_name="cidades", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_cidades_id", table_name="cidades", schema=DATABASE_SCHEMA)
    op.drop_table("cidades", schema=DATABASE_SCHEMA)

    op.drop_index("ix_gadm_empresas_nome", table_name="empresas", schema=DATABASE_SCHEMA)
    op.drop_index("ix_gadm_empresas_id", table_name="empresas", schema=DATABASE_SCHEMA)
    op.drop_table("empresas", schema=DATABASE_SCHEMA)


def _seed_initial_data() -> None:
    bind = op.get_bind()
    empresas = sa.table(
        "empresas",
        sa.column("id", sa.Integer()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.Text()),
        sa.column("cnpj", sa.String()),
        sa.column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )
    cidades = sa.table(
        "cidades",
        sa.column("id", sa.Integer()),
        sa.column("nome", sa.String()),
        sa.column("uf", sa.String()),
        sa.column("codigo_ibge", sa.String()),
        sa.column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )
    filiais = sa.table(
        "filiais",
        sa.column("empresa_id", sa.Integer()),
        sa.column("cidade_id", sa.Integer()),
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("tipo_unidade", sa.String()),
        sa.column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )
    departamentos = sa.table(
        "departamentos",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("descricao", sa.Text()),
        sa.column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )

    bind.execute(
        postgresql_insert(empresas)
        .values(nome="Urbi mobilidade", descricao=None, cnpj=None, ativo=True)
        .on_conflict_do_nothing(index_elements=[empresas.c.nome])
    )
    bind.execute(
        postgresql_insert(cidades)
        .values(nome="Brasilia", uf="DF", codigo_ibge=None, ativo=True)
        .on_conflict_do_nothing(index_elements=[cidades.c.nome, cidades.c.uf])
    )

    dados_filiais = sa.values(
        sa.column("nome", sa.String()),
        sa.column("tipo_unidade", sa.String()),
        name="dados_filiais",
    ).data(
        (
            ("Terminal", "TERMINAL"),
            ("Garagem Recanto", "GARAGEM"),
            ("Garagem Samambaia", "GARAGEM"),
            ("Escritorio Executivo", "ESCRITORIO"),
            ("Escritorio matriz", "ESCRITORIO"),
        )
    )
    empresa_id = sa.select(empresas.c.id).where(
        empresas.c.nome == "Urbi mobilidade"
    ).scalar_subquery()
    cidade_id = sa.select(cidades.c.id).where(
        cidades.c.nome == "Brasilia",
        cidades.c.uf == "DF",
    ).scalar_subquery()
    selecao_filiais = sa.select(
        empresa_id,
        cidade_id,
        sa.null(),
        dados_filiais.c.nome,
        dados_filiais.c.tipo_unidade,
        sa.true(),
    ).select_from(dados_filiais)
    bind.execute(
        postgresql_insert(filiais)
        .from_select(
            ["empresa_id", "cidade_id", "codigo", "nome", "tipo_unidade", "ativo"],
            selecao_filiais,
        )
        .on_conflict_do_nothing(index_elements=[filiais.c.empresa_id, filiais.c.nome])
    )

    codigos_departamentos = (
        "DCOL", "DP", "GADM", "G&C", "GDEN", "GIPE", "GMKT", "GOPE",
        "GPQS", "GPVE", "GRC", "GPSN", "GSMA", "GSOR", "GSUP", "GTRA", "GTSI",
    )
    bind.execute(
        postgresql_insert(departamentos)
        .values(
            [
                {"codigo": codigo, "nome": codigo, "descricao": None, "ativo": True}
                for codigo in codigos_departamentos
            ]
        )
        .on_conflict_do_nothing(index_elements=[departamentos.c.codigo])
    )

    localizacoes = sorted({nome for nome, _, _ in LOCALIZACAO_VINCULOS})
    localizacoes_table = sa.table(
        "localizacoes",
        sa.column("codigo", sa.String()),
        sa.column("nome", sa.String()),
        sa.column("tipo", sa.String()),
        sa.column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )
    op.bulk_insert(
        localizacoes_table,
        [
            {
                "codigo": None,
                "nome": nome,
                "tipo": _classificar_tipo_localizacao(nome),
                "ativo": True,
            }
            for nome in localizacoes
        ],
    )

    _seed_localizacao_vinculos(op.get_bind())


def _localizacao_vinculo_statement():
    metadata = sa.MetaData()
    localizacoes = sa.Table(
        "localizacoes",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    filiais = sa.Table(
        "filiais",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("empresa_id", sa.Integer()),
        sa.Column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    empresas = sa.Table(
        "empresas",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("nome", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    departamentos = sa.Table(
        "departamentos",
        metadata,
        sa.Column("id", sa.Integer()),
        sa.Column("codigo", sa.String()),
        schema=DATABASE_SCHEMA,
    )
    vinculos = sa.Table(
        "localizacao_vinculos",
        metadata,
        sa.Column("localizacao_id", sa.Integer()),
        sa.Column("filial_id", sa.Integer()),
        sa.Column("departamento_id", sa.Integer()),
        sa.Column("ativo", sa.Boolean()),
        schema=DATABASE_SCHEMA,
    )

    origem = (
        localizacoes.join(
            filiais,
            filiais.c.nome == sa.bindparam("filial"),
        )
        .join(
            empresas,
            sa.and_(
                empresas.c.id == filiais.c.empresa_id,
                empresas.c.nome == "Urbi mobilidade",
            ),
        )
        .join(
            departamentos,
            departamentos.c.codigo == sa.bindparam("departamento"),
        )
    )
    selecao = (
        sa.select(
            localizacoes.c.id,
            filiais.c.id,
            departamentos.c.id,
            sa.true(),
        )
        .select_from(origem)
        .where(localizacoes.c.nome == sa.bindparam("localizacao"))
    )
    return (
        postgresql_insert(vinculos)
        .from_select(
            ["localizacao_id", "filial_id", "departamento_id", "ativo"],
            selecao,
        )
        .on_conflict_do_nothing(
            index_elements=[
                vinculos.c.localizacao_id,
                vinculos.c.filial_id,
                vinculos.c.departamento_id,
            ]
        )
    )


def _seed_localizacao_vinculos(bind) -> None:
    bind.execute(
        _localizacao_vinculo_statement(),
        [
            {
                "localizacao": localizacao,
                "filial": filial,
                "departamento": departamento,
            }
            for localizacao, filial, departamento in LOCALIZACAO_VINCULOS
        ],
    )


def _classificar_tipo_localizacao(nome: str) -> str:
    prefixos = (
        ("SALA", "SALA"),
        ("PATIO", "PATIO"),
        ("TERMINAL", "TERMINAL"),
        ("PORTAO", "PORTAO"),
        ("PORTARIA", "PORTAO"),
        ("GUARITA", "PORTAO"),
        ("BANHEIRO", "BANHEIRO"),
        ("ESTACIONAMENTO", "ESTACIONAMENTO"),
        ("DEPOSITO", "DEPOSITO"),
        ("ALMOXARIFADO", "DEPOSITO"),
    )
    for prefixo, tipo in prefixos:
        if nome.startswith(prefixo):
            return tipo
    return "OUTRO"

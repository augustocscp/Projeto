"""atualiza seeds dos dominios patrimoniais

Revision ID: 0008
Revises: 0007
"""

from alembic import op
import sqlalchemy as sa

from app.config import DATABASE_SCHEMA

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

DOMINIOS = {
    "categorias_patrimoniais": (
        ("EQUIP_COMUNICACAO", "Equipamento de Comunicação e Monitoramento"),
        ("EQUIP_ELETRONICO_EMBARCADO", "Equipamento Eletrônico Embarcado"),
        ("EQUIP_INFORMATICA", "Equipamento de Informática"),
        ("MAQUINAS_EQUIPAMENTOS", "Máquinas e Equipamentos"),
        ("MARCAS_PATENTES", "Marcas e Patentes"),
        ("MOVEIS_UTENSILIOS", "Móveis e Utensílios"),
        ("VEICULOS", "Veículos"),
    ),
    "estados_conservacao": (
        ("NOVO", "Novo"), ("OTIMO", "Ótimo"), ("BOM", "Bom"),
        ("REGULAR", "Regular"), ("RUIM", "Ruim"), ("INSERVIVEL", "Inservível"),
    ),
    "situacoes_patrimoniais": (
        ("ATIVO", "Ativo"), ("EM_USO", "Em Uso"),
        ("DISPONIVEL", "Disponível"), ("EM_MANUTENCAO", "Em Manutenção"),
        ("EM_TRANSFERENCIA", "Em Transferência"), ("BAIXADO", "Baixado"),
        ("EXTRAVIADO", "Extraviado"), ("SINISTRADO", "Sinistrado"),
        ("ALIENADO", "Alienado"),
    ),
    "destinacoes_patrimoniais": (
        ("OPERACAO", "Operação"), ("ADMINISTRACAO", "Administração"),
        ("ALMOXARIFADO", "Almoxarifado"), ("RESERVA_TECNICA", "Reserva Técnica"),
        ("MANUTENCAO", "Manutenção"), ("TREINAMENTO", "Treinamento"),
        ("LOCADO", "Locado"), ("COMODATO", "Comodato"),
        ("DESCARTE", "Descarte"), ("VENDA", "Venda"),
    ),
}

REFERENCIAS = {
    "categorias_patrimoniais": "categoria_id",
    "estados_conservacao": "estado_conservacao_id",
    "situacoes_patrimoniais": "situacao_id",
    "destinacoes_patrimoniais": "destinacao_id",
}


def _aplicar(dominios: dict[str, tuple[tuple[str, str], ...]]) -> None:
    bind = op.get_bind()
    for tabela, registros in dominios.items():
        for ordem, (codigo, nome) in enumerate(registros, start=1):
            colunas = "codigo, nome, descricao, ativo"
            valores = ":codigo, :nome, NULL, true"
            atualizacao = "nome = EXCLUDED.nome, ativo = true, atualizado_em = now()"
            if tabela != "categorias_patrimoniais":
                colunas += ", ordem_exibicao"
                valores += ", :ordem"
                atualizacao += ", ordem_exibicao = EXCLUDED.ordem_exibicao"
            bind.execute(sa.text(
                f"INSERT INTO {DATABASE_SCHEMA}.{tabela} ({colunas}) VALUES ({valores}) "
                f"ON CONFLICT (codigo) DO UPDATE SET {atualizacao}"
            ), {"codigo": codigo, "nome": nome, "ordem": ordem})

        codigos = tuple(codigo for codigo, _ in registros)
        coluna_fk = REFERENCIAS[tabela]
        filtro = "d.codigo NOT IN :codigos AND " if codigos else ""
        comando = sa.text(
            f"DELETE FROM {DATABASE_SCHEMA}.{tabela} d WHERE {filtro}NOT EXISTS ("
            f"SELECT 1 FROM {DATABASE_SCHEMA}.patrimonios p WHERE p.{coluna_fk} = d.id)"
        )
        if codigos:
            comando = comando.bindparams(sa.bindparam("codigos", expanding=True))
            bind.execute(comando, {"codigos": codigos})
        else:
            bind.execute(comando)


def upgrade() -> None:
    _aplicar(DOMINIOS)


def downgrade() -> None:
    antigos = {
        "categorias_patrimoniais": (),
        "estados_conservacao": (("OTIMO", "Ótimo"), ("BOM", "Bom"), ("REGULAR", "Regular"), ("RUIM", "Ruim"),
                                ("DANIFICADO", "Danificado"), ("NAO_AVALIADO", "Não avaliado")),
        "situacoes_patrimoniais": (("EM_USO", "Em uso"), ("DISPONIVEL", "Disponível"),
                                   ("EM_MANUTENCAO", "Em manutenção"), ("RESERVA", "Reserva"),
                                   ("EXTRAVIADO", "Extraviado"), ("BAIXADO", "Baixado")),
        "destinacoes_patrimoniais": (("USO_INTERNO", "Uso interno"), ("COMODATO", "Comodato"), ("DOACAO", "Doação"),
                                     ("VENDA", "Venda"), ("TRANSFERENCIA", "Transferência"),
                                     ("SUCATA_DESCARTE", "Sucata/Descarte")),
    }
    _aplicar(antigos)

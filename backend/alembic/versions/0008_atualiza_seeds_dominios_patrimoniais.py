"""atualiza seeds dos dominios patrimoniais

Revision ID: 0008
Revises: 0007
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

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
        dominio = sa.table(
            tabela,
            sa.column("id", sa.Integer()),
            sa.column("codigo", sa.String()),
            sa.column("nome", sa.String()),
            sa.column("descricao", sa.Text()),
            sa.column("ativo", sa.Boolean()),
            sa.column("ordem_exibicao", sa.Integer()),
            sa.column("atualizado_em", sa.DateTime(timezone=True)),
            schema=DATABASE_SCHEMA,
        )
        coluna_fk = REFERENCIAS[tabela]
        patrimonios = sa.table(
            "patrimonios",
            sa.column(coluna_fk, sa.Integer()),
            schema=DATABASE_SCHEMA,
        )

        if registros:
            valores = [
                {
                    "codigo": codigo,
                    "nome": nome,
                    "descricao": None,
                    "ativo": True,
                    **(
                        {"ordem_exibicao": ordem}
                        if tabela != "categorias_patrimoniais"
                        else {}
                    ),
                }
                for ordem, (codigo, nome) in enumerate(registros, start=1)
            ]
            comando = postgresql_insert(dominio)
            atualizacao = {
                "nome": comando.excluded.nome,
                "ativo": True,
                "atualizado_em": sa.func.now(),
            }
            if tabela != "categorias_patrimoniais":
                atualizacao["ordem_exibicao"] = comando.excluded.ordem_exibicao
            comando = comando.on_conflict_do_update(
                index_elements=[dominio.c.codigo],
                set_=atualizacao,
            )
            bind.execute(comando, valores)

        codigos = tuple(codigo for codigo, _ in registros)
        sem_referencia = ~sa.exists(
            sa.select(1).where(patrimonios.c[coluna_fk] == dominio.c.id)
        )
        filtro = sem_referencia
        if codigos:
            filtro = sa.and_(dominio.c.codigo.not_in(codigos), sem_referencia)
        bind.execute(sa.delete(dominio).where(filtro))


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

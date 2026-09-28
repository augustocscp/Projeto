# Relatório de Implementação Final do Cadastro Patrimonial com BigQuery

## 1. Identificação da entrega

- Projeto: Sistema Patrimonial - Urbi Mobilidade
- Stack: FastAPI, SQLAlchemy, PostgreSQL, Alembic e Flutter Web
- Schema PostgreSQL: `gadm`
- Data da validação final: 28/09/2026
- Commit principal: `99aa067 - finaliza cadastro patrimonial com integracao BigQuery`
- Commit de ajuste dos testes: `10619c0 - alinha testes aos dominios patrimoniais finais`
- Impacto do commit principal: 45 arquivos, 1.479 inserções e 417 remoções

## 2. Resumo executivo

O módulo de cadastro patrimonial foi concluído com integração ao schema real do Protheus no BigQuery. A implementação substituiu o fluxo exploratório anterior por serviços específicos para dados cadastrais, contábeis e de responsáveis.

Foram adicionadas seis migrations, novos modelos de snapshot e histórico, regras de validação no backend, endpoints de consulta e atualização, além da adequação da interface Flutter para os novos campos obrigatórios e para a visualização detalhada do patrimônio.

O banco real foi migrado de `0007` para `0013`. A execução final confirmou que não havia patrimônios cadastrados e que os novos domínios foram aplicados sem deixar códigos antigos.

## 3. Migrations criadas

### 3.1. Migration 0008 - Domínios patrimoniais

Arquivo: `backend/alembic/versions/0008_atualiza_seeds_dominios_patrimoniais.py`

Responsabilidades:

- Inserir os sete códigos oficiais de categorias patrimoniais.
- Substituir os estados de conservação pelos seis códigos oficiais.
- Substituir as situações patrimoniais pelos nove códigos oficiais.
- Substituir as destinações patrimoniais pelos dez códigos oficiais.
- Remover códigos antigos somente quando não houver patrimônio referenciando o domínio.

Resultado no banco real:

- Categorias: 7 registros oficiais.
- Estados de conservação: 6 registros oficiais.
- Situações patrimoniais: 9 registros oficiais.
- Destinações patrimoniais: 10 registros oficiais.
- Patrimônios existentes durante a migration: 0.
- Patrimônios afetados pela substituição: nenhum.

### 3.2. Migration 0009 - Patrimônio, garantia e responsável

Arquivo: `backend/alembic/versions/0009_adiciona_campos_garantia_item_patrimonio.py`

Alterações em `gadm.patrimonios`:

- Adição de `numero_item`.
- Adição de `possui_garantia`.
- Adição de `codigo_produto`.
- Adição de `data_baixa_origem`.
- `codigo_protheus`, `numero_item` e `numero_serie` definidos como obrigatórios.
- Constraint única para `codigo_protheus + numero_item`.
- Check constraint para coerência entre garantia e data final da garantia.

Alterações em `gadm.responsaveis`:

- Adição de `departamento_externo` como texto livre.
- Adição de `gestor_responsavel` como texto livre.
- Adição de `consultado_em`.
- `departamento_id` alterado para nullable.
- Nenhuma FK foi criada para os novos campos externos.

### 3.3. Migration 0010 - Snapshot contábil

Arquivo: `backend/alembic/versions/0010_cria_patrimonios_contabeis.py`

Foi criada `gadm.patrimonios_contabeis`, com relacionamento único por patrimônio e armazenamento dos dados atuais de nota fiscal, fornecedor, aquisição, ICMS, depreciação, valor atual, conta contábil, centro de custo, baixa e dados brutos de SN1/SN3.

### 3.4. Migration 0011 - Histórico contábil

Arquivo: `backend/alembic/versions/0011_cria_historico_contabil.py`

Foi criada `gadm.historico_contabil`, com uma linha por campo contábil alterado. O histórico registra valor anterior, valor novo, origem, usuário e instante da consulta.

### 3.5. Migration 0012 - Histórico de controle patrimonial

Arquivo: `backend/alembic/versions/0012_cria_historico_controle_patrimonial.py`

Foi criada `gadm.historico_controle_patrimonial`. Cada PATCH compara os valores anteriores com os novos e grava uma linha por campo efetivamente alterado.

### 3.6. Migration 0013 - Histórico de sistema

Arquivo: `backend/alembic/versions/0013_cria_historico_sistema.py`

Foi criada `gadm.historico_sistema` para eventos técnicos e operacionais. Um trigger no PostgreSQL impede UPDATE e DELETE, garantindo comportamento append-only.

## 4. Integração BigQuery

### 4.1. Configuração

O `.env.example` passou a documentar as tabelas oficiais:

- `gcp-urbi-proj-operacao.silver.URBI_SN1`
- `gcp-urbi-proj-operacao.silver.URBI_SN3`
- `gcp-urbi-proj-manutencao.raw.SB1`
- `gcp-urbi-proj-operacao.security.funcionarios`
- `gcp-urbi-proj-manutencao.raw.CTT`

Foram removidas as configurações exploratórias de SNG e dos campos de filtro configuráveis.

### 4.2. Cliente BigQuery

O cliente genérico foi mantido com:

- Validação dos identificadores de tabela e campo.
- Suporte a tabelas totalmente qualificadas.
- Queries parametrizadas.
- Parâmetros tipados como STRING, BOOL, INT64 ou FLOAT64.
- Timeout configurável.
- Tradução de erros de configuração, autorização, tabela ausente e indisponibilidade.

### 4.3. Serviço cadastral

Arquivo: `backend/app/integrations/protheus_patrimonio_service.py`

Fluxo implementado:

1. Consulta SN1 por `N1_CBASE + N1_ITEM`.
2. Obtém produto e descrição.
3. Consulta SB1 por `B1_COD`.
4. Retorna código do produto, descrição, modelo e fabricante.

Não existe leitura de `N1_PATRIM`.

### 4.4. Serviço contábil

Arquivo: `backend/app/integrations/protheus_contabil_service.py`

O serviço consulta SN1 e SN3 pelo código-base e item. Toda consulta à SN3 inclui obrigatoriamente:

`N3_TIPO = '10'`

São normalizados os dados de nota fiscal, fornecedor, aquisição, ICMS, depreciação, valor atual, conta contábil, centro de custo e baixa. O valor atual é calculado por aquisição menos depreciação acumulada.

Quando existem múltiplos registros contábeis após o filtro, o primeiro é usado como fallback e a inconsistência é registrada. Divergências entre baixa da SN1 e da SN3 geram evento `DIVERGENCIA_BAIXA`.

### 4.5. Serviço de responsável

Arquivo: `backend/app/integrations/protheus_responsavel_service.py`

O fluxo local-first foi implementado:

1. Busca o RE em `gadm.responsaveis`.
2. Se existir e estiver ativo, utiliza o snapshot local sem nova consulta.
3. Se não existir e a integração estiver desativada, retorna HTTP 503.
4. Se a integração estiver ativa, consulta funcionários com `MATRICULA`, `IS_CURRENT=true` e `CODSITUACAO='A'`.
5. Se não encontrar, executa consulta diagnóstica com `MATRICULA + IS_CURRENT=true`.
6. Consulta CTT diretamente por `CTT_DESC01`.
7. Persiste o responsável com `origem_dados='API'`.

`CTT_XRESPO` é armazenado exatamente como recebido, sem parsing ou normalização.

## 5. Regras de negócio implementadas

- `numero_tombo` permanece gerado exclusivamente pela sequence interna.
- `codigo_protheus`, `numero_item` e `numero_serie` são obrigatórios.
- A combinação `codigo_protheus + numero_item` é única.
- A plaqueta física continua manual e única.
- Número de série continua manual e não usa `N1_NSERIE`.
- Garantia continua manual.
- Garantia marcada como presente exige data final.
- Garantia ausente exige data final nula.
- Localização é validada por `localizacao_vinculos`.
- Filial do tipo TERMINAL aceita somente localização do tipo TERMINAL.
- Cidade é derivada da filial e retornada como informação somente leitura.
- Nenhum campo de localização aceita valor nulo ou a opção textual "Todos".
- Patrimônio baixado, alienado, extraviado ou sinistrado não pode ser movimentado.
- `data_baixa_origem` também bloqueia movimentação.
- O código de erro do bloqueio é `PATRIMONIO_BAIXADO_NAO_MOVIMENTAVEL`.
- Não foi implementada exclusão física de patrimônio, snapshot ou histórico.

## 6. API

Endpoints adicionados ou consolidados:

- `GET /api/patrimonios/protheus-cadastral`
- `GET /api/patrimonios/protheus-contabil`
- `GET /api/responsaveis/protheus`
- `POST /api/patrimonios`
- `PATCH /api/patrimonios/{id}`
- `GET /api/patrimonios/{id}`
- `GET /api/patrimonios/{id}/historico`
- `PATCH /api/patrimonios/{id}/inativar`

Comportamento do detalhe:

- A listagem utiliza somente o snapshot armazenado.
- O detalhe atualiza os dados contábeis de forma síncrona quando a integração está ativa.
- Em falha técnica, retorna o snapshot em cache e registra `FALHA_INTEGRACAO`.
- Integração desativada não é tratada como falha técnica.

O endpoint de histórico agrega:

- Histórico contábil.
- Histórico de controle patrimonial.
- Histórico de sistema.

## 7. Interface Flutter Web

O formulário patrimonial foi atualizado com:

- Código Protheus obrigatório.
- Número do item obrigatório.
- Número de série obrigatório.
- Controle de garantia por switch.
- Data de garantia habilitada somente quando necessária.
- RE do responsável no lugar da seleção direta por ID.
- Consulta cadastral e contábil ao Protheus.
- Preenchimento de descrição, modelo e fabricante a partir da consulta.
- Cidade exibida automaticamente após a escolha da filial.
- Remoção da entrada manual de data de baixa.

Foi adicionada uma ação de detalhe na listagem. A tela de detalhe chama o endpoint que atualiza o snapshot contábil e apresenta identificação, responsável, dados contábeis, data da última consulta e quantidade de eventos históricos.

## 8. Autenticação de desenvolvimento

As alterações locais que já estavam pendentes foram consolidadas na entrega:

- Endpoint `POST /auth/dev-login`.
- Criação de usuário e sessão reais no banco.
- Cookie HTTP-only com a mesma política da autenticação normal.
- Proteção por `DEV_AUTH_BYPASS`.
- Valor padrão documentado: `false`.

## 9. Componentes exploratórios removidos

Foram removidos os componentes anteriores baseados em SN1/SN3/SNG genéricos:

- Router exploratório antigo.
- Schema exploratório antigo.
- Serviço de staging exploratório antigo.
- Serviço Protheus BigQuery sem mapeamento real.
- Tipos raw provisórios.

A tabela `integracao_bigquery_staging`, criada na migration `0007`, foi preservada conforme a orientação de não alterar ou recriar estruturas anteriores.

## 10. Testes e validações

Foram cobertos:

- Aplicação das migrations e seeds oficiais.
- Garantia com e sem data.
- Validação de responsável.
- Filtro obrigatório `N3_TIPO='10'`.
- Filtros `IS_CURRENT=true` e `CODSITUACAO='A'`.
- Consulta diagnóstica de responsável inativo.
- Preservação textual de `CTT_XRESPO`.
- Endpoints com integração desativada.
- Criação, atualização e inativação patrimonial.
- Histórico contábil somente quando existe divergência.
- Histórico por campo alterado via PATCH.
- Evento de divergência de baixa.
- Bloqueio de movimentação de patrimônio baixado.
- Rejeição de "Todos" nos campos de localização.
- Geração concorrente e única do número de tombo.

Resultado final:

- 26 testes aprovados.
- 0 testes com falha.
- Migrations executadas em schema temporário durante os testes.
- Migrations executadas no schema real `gadm`.
- Revisão final do banco: `0013`.

Os avisos remanescentes são depreciações futuras em FastAPI, Starlette e Alembic, sem impacto funcional na entrega.

## 11. Estado final

- Banco real em `0013`.
- Domínios oficiais confirmados por consulta direta.
- Nenhum patrimônio existente ou afetado na substituição dos seeds.
- Worktree limpo após os commits da implementação e dos testes.
- Branch `main` seis commits à frente de `origin/main` antes da inclusão deste relatório.

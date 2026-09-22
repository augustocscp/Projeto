# Relatório de alterações do Sistema Patrimonial

**Data do relatório:** 22/09/2026
**Projeto:** Sistema Patrimonial
**Escopo:** persistência de usuários e sessões, adoção do Alembic, estrutura organizacional e carga normalizada de localizações.

## 1. Objetivo

Este documento consolida as alterações identificadas no último trabalho relacionado ao banco de dados e na correção posterior da carga de localizações.

O relatório foi elaborado a partir:

- do estado atual dos arquivos do projeto;
- do histórico Git disponível;
- das migrations `0001` e `0002`;
- da planilha `Localizacoes.xlsx`;
- das verificações realizadas durante a implementação.

O histórico textual do outro chat não está disponível nesta conversa. Por isso, o relatório descreve apenas alterações comprovadas pelos arquivos e commits existentes.

## 2. Resumo executivo

Foram implementados três blocos principais:

1. Persistência de usuários autenticados e sessões no PostgreSQL.
2. Controle explícito da evolução do banco com Alembic e criação da estrutura organizacional.
3. Correção da modelagem de localizações para manter um nome único e vários vínculos válidos com filiais e departamentos.

Ao final das alterações, o modelo contém:

- usuários;
- sessões autenticadas;
- empresas;
- cidades;
- filiais;
- departamentos;
- localizações únicas;
- vínculos entre localização, filial e departamento.

A planilha fornecida possui 172 relacionamentos, convertidos em 134 localizações únicas e 172 vínculos.

## 3. Alteração anterior: persistência de usuários e sessões

O histórico Git registra o commit `444236f`, com a descrição `Adiciona persistencia de sessoes`.

### 3.1 Banco de dados e SQLAlchemy

Foi criada a configuração central do SQLAlchemy em `backend/app/database.py`:

- metadata vinculada ao schema configurável do PostgreSQL;
- engine com verificação de conexão por `pool_pre_ping`;
- timeout de conexão de 5 segundos;
- fábrica de sessões `SessionLocal`;
- dependência `get_db()` para abrir e fechar sessões por requisição;
- função opcional `create_database_objects()` para criação direta pelo SQLAlchemy.

A URL do banco é carregada da variável `DATABASE_URL`. Usuário e senha são normalizados e codificados antes da criação da engine, evitando erros quando as credenciais contêm caracteres especiais.

### 3.2 Modelo de usuários

Foi criado o modelo `Usuario` em `backend/app/models/usuario.py` com:

| Campo | Finalidade |
| --- | --- |
| `id` | Identificador interno |
| `azure_oid` | Identificador único do usuário no Microsoft Entra ID |
| `nome` | Nome apresentado pelo provedor de identidade |
| `email` | E-mail único do usuário |
| `cargo` | Cargo ou função administrativa |
| `filial` | Filial associada ao usuário |
| `perfil` | Perfil de autorização |
| `ativo` | Controle de habilitação do usuário |
| `criado_em` | Data de criação |
| `atualizado_em` | Data da última atualização |

Foram configuradas unicidade e indexação para `azure_oid` e `email`.

### 3.3 Modelo de sessões

Foi criado o modelo `Sessao` em `backend/app/models/sessao.py` com:

| Campo | Finalidade |
| --- | --- |
| `id` | Identificador da sessão |
| `token_hash` | Hash SHA-256 do token armazenado no cookie |
| `usuario_id` | Chave estrangeira para o usuário |
| `criado_em` | Início da sessão |
| `expira_em` | Limite de validade |
| `ultimo_acesso_em` | Última utilização válida |
| `revogado_em` | Momento do encerramento ou revogação |

O token original não é armazenado no banco. Apenas o hash é persistido.

### 3.4 Fluxo de autenticação Microsoft

O arquivo `backend/app/auth.py` passou a controlar o fluxo de autenticação com Microsoft Entra ID por meio da biblioteca MSAL.

O fluxo implementado é:

1. `GET /auth/login` gera a URL de autorização Microsoft.
2. `GET /auth/callback` troca o código recebido por tokens e lê os dados do usuário.
3. O usuário é criado ou atualizado no banco utilizando o `azure_oid`.
4. Uma sessão de oito horas é criada.
5. Um token aleatório é enviado em cookie `HttpOnly`.
6. `GET /auth/me` valida a sessão e devolve os dados do usuário autenticado.
7. `POST /auth/logout` revoga a sessão e remove o cookie.
8. `GET /auth/logout` também encerra a sessão Microsoft no navegador.

As rotas protegidas usam `get_current_user()`, que verifica:

- existência do cookie;
- correspondência do hash no banco;
- expiração da sessão;
- eventual revogação;
- existência e situação ativa do usuário.

O último acesso da sessão é atualizado após uma validação bem-sucedida.

### 3.5 Migration `0001`

A migration `backend/alembic/versions/0001_cria_usuarios_e_sessoes.py` reproduz no banco a estrutura de usuários e sessões.

Ela executa:

- criação do schema configurado, caso ainda não exista;
- criação da tabela `usuarios`;
- criação da tabela `sessoes`;
- criação das chaves únicas;
- criação das chaves estrangeiras;
- criação dos índices usados na autenticação;
- procedimento de downgrade em ordem segura, removendo primeiro sessões e depois usuários.

## 4. Alteração anterior: adoção do Alembic

Foi adicionada a estrutura de migrations em `backend/alembic/` e o arquivo `backend/alembic.ini`.

### 4.1 Configuração

O Alembic foi configurado para:

- usar `backend/alembic` como diretório de scripts;
- carregar a URL do banco a partir da configuração da aplicação;
- importar todos os modelos registrados em `app.models`;
- considerar múltiplos schemas;
- manter a tabela de versão dentro do schema configurado;
- suportar execução online e geração offline de SQL;
- criar o schema antes de executar as migrations.

A dependência `alembic` foi incluída em `backend/requirements.txt`.

### 4.2 Controle da criação automática

Foi adicionada a variável `AUTO_CREATE_DATABASE_OBJECTS` em `backend/app/config.py`.

Comportamento atual:

- valor padrão: `false`;
- quando `false`, o início da API não executa `Base.metadata.create_all()`;
- quando `true`, a criação automática continua disponível para cenários controlados.

Essa alteração evita que a aplicação altere o schema silenciosamente durante a inicialização e deixa o Alembic como mecanismo principal de evolução do banco.

## 5. Alteração anterior: estrutura organizacional

Foram criados modelos para representar a estrutura usada pelo sistema patrimonial.

### 5.1 Empresa

Arquivo: `backend/app/models/empresa.py`.

Principais regras:

- nome único;
- CNPJ opcional;
- descrição opcional;
- controle de ativo;
- relacionamento com filiais.

### 5.2 Cidade

Arquivo: `backend/app/models/cidade.py`.

Principais regras:

- combinação única de nome e UF;
- código IBGE opcional;
- controle de ativo;
- relacionamento com filiais.

### 5.3 Filial

Arquivo: `backend/app/models/filial.py`.

Principais regras:

- vínculo obrigatório com empresa e cidade;
- nome único dentro da empresa;
- tipos aceitos: `TERMINAL`, `GARAGEM` ou `ESCRITORIO`;
- controle de ativo;
- relacionamento com os vínculos de localização.

### 5.4 Departamento

Arquivo: `backend/app/models/departamento.py`.

Principais regras:

- código único;
- nome e descrição;
- controle de ativo;
- relacionamento com os vínculos de localização.

### 5.5 Registro central dos modelos

O arquivo `backend/app/models/__init__.py` passou a importar e expor todos os modelos.

Isso permite que o SQLAlchemy e o Alembic descubram a estrutura completa usando apenas `import app.models`.

## 6. Alteração atual: correção da modelagem de localizações

### 6.1 Problema identificado

O desenho inicial armazenava `filial_id` e `departamento_id` diretamente na tabela `localizacoes`.

Esse desenho obrigava a duplicação do nome da localização quando:

- a mesma localização existia em filiais diferentes;
- a mesma localização pertencia a departamentos diferentes;
- a mesma localização precisava representar várias combinações de filial e departamento.

Exemplos da planilha:

- `MURO` possui dois vínculos, um para `Garagem Recanto` e outro para `Garagem Samambaia`;
- `COORDENAÇÃO` possui 14 vínculos, distribuídos entre departamentos e filiais diferentes;
- `SALA DA GERENCIA` possui três departamentos distintos na mesma filial.

### 6.2 Solução adotada

A modelagem foi normalizada em duas tabelas.

#### Tabela `localizacoes`

Armazena o cadastro único da localização:

- `id`;
- `codigo` opcional;
- `nome` único;
- `tipo`;
- `ativo`;
- datas de criação e atualização.

#### Tabela `localizacao_vinculos`

Armazena cada combinação válida:

- `localizacao_id`;
- `filial_id`;
- `departamento_id`;
- `ativo`;
- datas de criação e atualização.

A combinação `localizacao_id + filial_id + departamento_id` é única.

Foi utilizada uma única tabela associativa para preservar as combinações reais. Duas relações independentes, uma para filiais e outra para departamentos, produziriam combinações por cruzamento que não existem na planilha.

### 6.3 Relacionamentos SQLAlchemy

Foram configurados os seguintes relacionamentos:

- `Localizacao.vinculos`;
- `LocalizacaoVinculo.localizacao`;
- `LocalizacaoVinculo.filial`;
- `LocalizacaoVinculo.departamento`;
- `Filial.localizacao_vinculos`;
- `Departamento.localizacao_vinculos`.

Os relacionamentos principais usam exclusão em cascata para os registros associativos.

## 7. Carga da planilha de localizações

Fonte utilizada: `Localizacoes.xlsx`, aba `Planilha1`, intervalo `A1:E173`.

Colunas encontradas:

| Coluna | Conteúdo |
| --- | --- |
| Empresa | Empresa responsável |
| Descrição | Nome da localização |
| Filial | Unidade relacionada |
| Departamento | Código do departamento |
| Cidade | Cidade da filial |

### 7.1 Resultado da análise

| Item | Quantidade |
| --- | ---: |
| Linhas de relacionamento | 172 |
| Linhas vazias | 0 |
| Linhas exatamente duplicadas | 0 |
| Empresas | 1 |
| Cidades | 1 |
| Filiais | 5 |
| Departamentos | 17 |
| Localizações únicas | 134 |

### 7.2 Dados organizacionais carregados

Empresa:

- `Urbi mobilidade`.

Cidade:

- `Brasilia`, UF `DF`.

Filiais:

- `Terminal`;
- `Garagem Recanto`;
- `Garagem Samambaia`;
- `Escritorio Executivo`;
- `Escritorio matriz`.

Departamentos:

- `DCOL`;
- `DP`;
- `GADM`;
- `G&C`;
- `GDEN`;
- `GIPE`;
- `GMKT`;
- `GOPE`;
- `GPQS`;
- `GPVE`;
- `GRC`;
- `GPSN`;
- `GSMA`;
- `GSOR`;
- `GSUP`;
- `GTRA`;
- `GTSI`.

### 7.3 Normalização aplicada

Os espaços no início e no final dos valores foram removidos antes da incorporação à migration.

Isso evita que valores como `MURO` e `MURO ` sejam tratados como localizações distintas.

Os nomes foram mantidos conforme a planilha, sem correção automática de acentos ou mudança de capitalização.

### 7.4 Classificação dos tipos

Como a planilha não possui uma coluna específica para o tipo da localização, a migration classifica nomes por prefixo:

| Prefixo | Tipo atribuído |
| --- | --- |
| `SALA` | `SALA` |
| `PATIO` | `PATIO` |
| `TERMINAL` | `TERMINAL` |
| `PORTAO`, `PORTARIA`, `GUARITA` | `PORTAO` |
| `BANHEIRO` | `BANHEIRO` |
| `ESTACIONAMENTO` | `ESTACIONAMENTO` |
| `DEPOSITO`, `ALMOXARIFADO` | `DEPOSITO` |
| demais nomes | `OUTRO` |

Os valores aceitos são protegidos por uma restrição `CHECK` no banco.

## 8. Migration `0002`

A migration `backend/alembic/versions/0002_cria_estrutura_organizacional_e_localizacoes.py` depende da revisão `0001`.

Ela executa, nesta ordem:

1. criação do schema, se necessário;
2. criação de `empresas`;
3. criação de `cidades`;
4. criação de `filiais`;
5. criação de `departamentos`;
6. criação de `localizacoes`;
7. criação de `localizacao_vinculos`;
8. inclusão da empresa e cidade;
9. inclusão das cinco filiais;
10. inclusão dos 17 departamentos;
11. inclusão das 134 localizações únicas;
12. inclusão dos 172 vínculos da planilha.

O downgrade remove os índices e tabelas na ordem inversa, respeitando as chaves estrangeiras.

## 9. Validações executadas

Foram executadas as seguintes verificações:

### 9.1 Comparação planilha versus migration

Resultado:

- 172 linhas na planilha;
- 172 vínculos incorporados à migration;
- 134 nomes únicos em ambos;
- nenhuma linha ausente;
- nenhuma linha adicional;
- mesma ordem dos registros;
- nenhuma linha vazia;
- nenhuma combinação exatamente duplicada.

### 9.2 Compilação Python

Todos os arquivos Python do backend foram compilados sem erro.

### 9.3 Mapeamentos SQLAlchemy

`configure_mappers()` foi executado com sucesso.

Foram confirmadas no metadata as tabelas:

- `gadm.departamentos`;
- `gadm.filiais`;
- `gadm.localizacoes`;
- `gadm.localizacao_vinculos`.

### 9.4 Alembic

O Alembic reconheceu a cadeia:

```text
0001 -> 0002 (head)
```

A geração offline do SQL para `upgrade head` foi concluída sem erro, produzindo 533 linhas de SQL.

## 10. Arquivos envolvidos

### Autenticação e sessões

- `backend/app/auth.py`;
- `backend/app/models/usuario.py`;
- `backend/app/models/sessao.py`;
- `backend/alembic/versions/0001_cria_usuarios_e_sessoes.py`.

### Configuração de banco e migrations

- `backend/app/config.py`;
- `backend/app/database.py`;
- `backend/app/main.py`;
- `backend/app/models/__init__.py`;
- `backend/alembic.ini`;
- `backend/alembic/env.py`;
- `backend/alembic/script.py.mako`;
- `backend/requirements.txt`.

### Estrutura organizacional e localizações

- `backend/app/models/empresa.py`;
- `backend/app/models/cidade.py`;
- `backend/app/models/filial.py`;
- `backend/app/models/departamento.py`;
- `backend/app/models/localizacao.py`;
- `backend/alembic/versions/0002_cria_estrutura_organizacional_e_localizacoes.py`;
- `Localizacoes.xlsx`.

## 11. Estado atual e pendências

### Concluído

- modelagem dos usuários e sessões;
- autenticação com persistência de sessão;
- migrations `0001` e `0002`;
- configuração do Alembic;
- modelos da estrutura organizacional;
- normalização das localizações;
- incorporação integral da planilha à migration;
- validação estática dos modelos e migrations.

### Ainda não executado

- aplicação de `alembic upgrade head` no PostgreSQL configurado;
- validação das contagens diretamente no banco após a migration;
- testes de integração contra um banco PostgreSQL real;
- criação de endpoints CRUD para empresas, cidades, filiais, departamentos e localizações;
- criação de filtros de localização por filial e departamento;
- commit das alterações atualmente presentes no diretório de trabalho.

## 12. Comando previsto para aplicação

Na raiz do projeto:

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Esse comando altera o banco configurado em `backend/.env` e deve ser executado apenas após confirmação do ambiente de destino e existência de backup quando aplicável.

## 13. Resultado esperado após a aplicação

Após a execução bem-sucedida das migrations, o banco deverá conter:

| Entidade | Quantidade inicial esperada |
| --- | ---: |
| Empresa | 1 |
| Cidade | 1 |
| Filiais | 5 |
| Departamentos | 17 |
| Localizações | 134 |
| Vínculos de localização | 172 |

As quantidades de usuários e sessões dependerão dos acessos realizados pela autenticação Microsoft.

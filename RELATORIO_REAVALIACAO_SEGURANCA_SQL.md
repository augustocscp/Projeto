# Relatorio de reavaliacao de seguranca SQL

Data: 2026-10-02

## Escopo

Reavaliacao integral dos apontamentos Semgrep relacionados a SQLAlchemy, SQL
formatado, corpo `pass` em downgrade e falsos positivos de `return` nos models de
historico. A revisao incluiu todas as ocorrencias equivalentes encontradas no
backend, e nao apenas as linhas inicialmente reportadas.

## Correcoes realizadas

- removidas todas as ocorrencias de `sa.text(f"...")`, `text(f"...")`,
  `execute(f"...")` e `op.execute(f"...")`;
- seeds, updates, deletes, CTEs e `INSERT ... FROM SELECT` reescritos com
  SQLAlchemy Core e `postgresql.insert`;
- valores variaveis mantidos como parametros vinculados;
- tabelas, colunas e schemas representados por objetos SQLAlchemy;
- sequence `patrimonio_numero_tombo_seq` criada, removida e referenciada por
  `Sequence(..., schema=DATABASE_SCHEMA)`;
- DDL PostgreSQL da funcao e trigger encapsulado em `DDL`, com schema quoted
  pelo preparador do dialeto;
- helpers com tabela/coluna dinamicas passaram a validar uma whitelist fechada;
- downgrades vazios e o template Alembic usam `return None`;
- lambdas de timestamp dos historicos foram substituidas por funcoes nomeadas.

## Validacoes executadas

- validacao de `DATABASE_SCHEMA`, incluindo casos invalidos e limites 63/64;
- upgrades online ate `0019` em schema temporario exclusivo;
- downgrades e novos upgrades das revisoes `0006`, `0015`, `0016`, `0017` e
  `0018`;
- `upgrade head` repetido;
- carga dos vinculos executada repetidamente, permanecendo em 172 combinacoes
  distintas;
- verificacao de tabelas, seeds, sequence, funcao, trigger e versao Alembic;
- geracao offline de `upgrade head --sql` em processo isolado;
- verificacao da ordem de `CREATE SCHEMA` e ausencia de referencias a `gadm` ou
  `public` no SQL offline;
- manifesto antes/depois de tabelas, views, sequences, indices, constraints,
  funcoes, triggers, tipos e extensoes nos namespaces preexistentes;
- confirmacao do OID/proprietario do schema temporario antes do `DROP SCHEMA`;
- preservacao conjunta da falha original e de eventual falha de limpeza.

Resultado da suite:

```text
45 passed, 194 warnings in 384.72s (0:06:24)
```

Os warnings sao deprecacoes de FastAPI/Starlette/Alembic e indisponibilidade do
cache local do pytest; nenhum corresponde a falha funcional ou de seguranca.

## Resultado SAST

Comando equivalente executado localmente com a imagem oficial do Semgrep:

```text
semgrep scan --config p/python --metrics=off --json /src/backend
```

- Semgrep OSS: 1.178.0;
- imagem: `semgrep/semgrep:latest`;
- digest: `sha256:32e459968daabe7ab86968184a29109b9564aa00392401156f9788452b42786b`;
- regras executadas: 151;
- arquivos Python analisados: 67;
- erros de analise: 0;
- achados: 0;
- achados bloqueantes: 0.

## Parecer para o analista

Os 18 apontamentos informados e as ocorrencias equivalentes encontradas na
revisao transversal foram removidos. Nao ha mais composicao de consultas por
f-string nos sinks SQLAlchemy auditados. O SQL textual remanescente limita-se a
defaults estaticos (`true` e `now()`) e DDL PostgreSQL encapsulado em `DDL`, sem
dados externos ou identificadores nao tratados.

As migrations mantiveram equivalencia estrutural e funcional, os 172 vinculos
permaneceram idempotentes, nenhum objeto escapou do schema temporario e o
manifesto dos namespaces preexistentes permaneceu inalterado. A reavaliacao SAST
com o pacote Python que contem as regras reportadas concluiu sem achados.

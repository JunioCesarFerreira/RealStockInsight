# Banco de dados PostgreSQL

Neste diretório estão os arquivos necessários para configurar e executar um contêiner Docker do PostgreSQL. O Dockerfile cria uma imagem com o Postgres instalado e expõe a porta 5432. O script `schema.sql` é utilizado para criar a tabela utilizada.

## Configuração e Execução

Siga as instruções abaixo para configurar e executar o projeto:

### 1. Configurar o ambiente

Certifique-se de ter as seguintes ferramentas e dependências instaladas:

- Docker

### 2. Configurar e iniciar o postgreSQL

No diretório `postgresql`, execute os seguintes comandos para configurar e iniciar o Cassandra em um contêiner Docker:

```sh
docker build -t postgres-db .
docker run -d --name postgres-db -p 5432:5432 postgres-db
```


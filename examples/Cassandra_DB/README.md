# API de Dados com Cassandra, Python e Go

Este é um projeto que consiste em um serviço Python para registrar dados em formato JSON em um banco de dados Apache Cassandra e uma API Go (Golang) para acessar esses dados. A API retorna o JSON mais recetente postado.
O projeto é dividido em três diretórios:

1. **cassandra-db**: Contém os arquivos necessários para configurar e executar um contêiner Docker do Apache Cassandra. O Dockerfile cria uma imagem com o Cassandra instalado e expõe a porta 9042. O script `init-cassandra.sh` copia um arquivo CQL de inicialização para o contêiner e executa o script para criar um keyspace e uma tabela no Cassandra.

2. **data-recorder**: Este diretório contém um script Python que gera dados em formato JSON e os insere no banco de dados Cassandra. Ele usa a biblioteca `cassandra-driver` para interagir com o Cassandra e a biblioteca `networkx` para criar e modificar grafos de exemplo.

3. **go-api**: Aqui está a API Go que fornece acesso aos dados armazenados no Cassandra. Ela usa o framework Gin para criar as rotas HTTP. A API se conecta ao Cassandra usando a biblioteca `gocql` e responde a solicitações GET com os dados JSON armazenados.

## Configuração e Execução

Siga as instruções abaixo para configurar e executar o projeto:

### 1. Configurar o ambiente

Certifique-se de ter as seguintes ferramentas e dependências instaladas:

- Python
- Go (Golang)
- Docker

### 2. Configurar e iniciar o Apache Cassandra

No diretório `cassandra-db`, execute os seguintes comandos para configurar e iniciar o Cassandra em um contêiner Docker:

```sh
docker build -t cassandra-db .
docker run -d --name cassandra-db -p 9042:9042 cassandra-db
```

Em seguida, execute o script `init-cassandra.sh` para criar o keyspace e a tabela no Cassandra:

```sh
./init-cassandra.sh
```

### 3. Instalar o driver Cassandra para Python

Certifique-se de ter o driver `cassandra-driver` instalado no Python. Você pode instalá-lo usando o `pip`:

```sh
pip install cassandra-driver
```

### 4. Inserir dados no Cassandra

No diretório `data-recorder`, execute o script Python para inserir dados no Cassandra:

```sh
python data_recorder.py
```

Este script gera dados de exemplo e os insere no Cassandra. Ele gera 10 grafos diferentes para demonstração.

### 5. Instalar o driver Cassandra para Go

Certifique-se de ter o driver `gocql` instalado no Go. Você pode instalá-lo usando o `go get`:

```sh
go get github.com/gocql/gocql
```

### 6. Executar a API Go

No diretório `go-api`, execute o seguinte comando para iniciar a API Go:

```sh
go run main.go
```

A API estará disponível em `http://localhost:5000/getdata`.

### 7. Acessar dados

Você pode acessar os dados JSON armazenados no Cassandra fazendo uma solicitação GET para a API em `http://localhost:5000/getdata`. A resposta será um JSON contendo os dados armazenados.

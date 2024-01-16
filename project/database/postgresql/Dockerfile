FROM postgres:latest

# Define as variáveis de ambiente para o banco de dados, usuário e senha
ENV POSTGRES_DB=database
ENV POSTGRES_USER=userDb
ENV POSTGRES_PASSWORD=password1234

# Copia arquivo SQL para o diretório de inicialização do Docker
COPY schema.sql /docker-entrypoint-initdb.d/schema.sql

# Permissões para o script SQL
RUN chmod -R 755 /docker-entrypoint-initdb.d

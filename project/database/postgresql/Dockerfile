FROM postgres:18.6

# Define as variáveis de ambiente para o banco de dados e usuário
ENV POSTGRES_DB=database
ENV POSTGRES_USER=userDb
# POSTGRES_PASSWORD deve ser fornecida em tempo de execucao (ver docker-compose.yaml / .env)

# Copia arquivo SQL para o diretório de inicialização do Docker
COPY schema.sql /docker-entrypoint-initdb.d/schema.sql

# Permissões para o script SQL
RUN chmod -R 755 /docker-entrypoint-initdb.d

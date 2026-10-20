FROM nginx:1.31.7

# Instala o Netcat e o OpenSSL
RUN apt-get update && \
    apt-get install -y netcat-traditional openssl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Certificado autoassinado (valido por 1 ano).
# Ajuste CERT_HOST para o hostname/IP usado no acesso (ex.: --build-arg CERT_HOST=meu.host).
ARG CERT_HOST=localhost
RUN mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -keyout /etc/nginx/ssl/selfsigned.key \
      -out /etc/nginx/ssl/selfsigned.crt \
      -subj "/CN=${CERT_HOST}" \
      -addext "subjectAltName=DNS:${CERT_HOST},DNS:localhost,IP:127.0.0.1" && \
    chmod 600 /etc/nginx/ssl/selfsigned.key

COPY nginx.conf /etc/nginx/nginx.conf
COPY mime.types /etc/nginx/mime.types
COPY init-nginx.sh /init-nginx.sh

RUN chmod +x /init-nginx.sh

CMD ["/init-nginx.sh"]

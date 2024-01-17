FROM nginx:latest

# Instala o Netcat
RUN apt-get update && \
    apt-get install -y netcat-traditional && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY mime.types /etc/nginx/mime.types
COPY init-nginx.sh /init-nginx.sh

RUN chmod +x /init-nginx.sh

CMD ["/init-nginx.sh"]

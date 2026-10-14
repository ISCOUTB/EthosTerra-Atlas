# === Etapa 1: Construcción (Builder) ===
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_URL=/v2
ENV VITE_API_URL=$VITE_API_URL

# Copiar configuración e instalar dependencias con npm
COPY package.json ./
RUN npm install

# Copiar el código fuente y compilar artefactos estáticos con Vite
COPY . .
RUN npm run build

# === Etapa 2: Servidor Web Estático y Proxy Inverso Unificado ===
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

RUN printf '%s\n' \
    'server {' \
    '    listen 80;' \
    '    client_max_body_size 100M;' \
    '    location / {' \
    '        root /usr/share/nginx/html;' \
    '        index index.html;' \
    '        try_files $uri $uri/ /index.html;' \
    '    }' \
    '    location /v2/ {' \
    '        proxy_pass http://api:8000/v2/;' \
    '        proxy_set_header Host $host;' \
    '        proxy_set_header X-Real-IP $remote_addr;' \
    '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' \
    '        proxy_set_header X-Forwarded-Proto $scheme;' \
    '        proxy_read_timeout 300s;' \
    '    }' \
    '    location /health {' \
    '        proxy_pass http://api:8000/health;' \
    '        proxy_set_header Host $host;' \
    '    }' \
    '}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

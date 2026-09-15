# === Etapa 1: Construcción (Builder) ===
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar configuración e instalar con npm (evita el error ERR_PNPM_MINIMUM_RELEASE_AGE_VIOLATION)
COPY package.json ./
RUN npm install

# Copiar el resto del código y compilar Vite/React
COPY . .
RUN npm run build

# === Etapa 2: Servidor Web Estático (Producción/Inferencia) ===
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

RUN echo "server { \
    listen 5173; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files \$uri \$uri/ /index.html; \
    } \
}" > /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]

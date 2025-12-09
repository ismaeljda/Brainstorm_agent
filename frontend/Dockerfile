# Dockerfile pour frontend React
FROM node:20-alpine AS builder

WORKDIR /app

# Copier package files
COPY package.json package-lock.json* ./

# Installer les dépendances
RUN npm install

# Copier le code source
COPY . .

# Build de production
RUN npm run build

# Stage production avec nginx
FROM nginx:alpine

# Copier le build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier config nginx custom
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

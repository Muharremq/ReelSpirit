# --- Aşama 1: Build (Derleme) ---
FROM node:20-alpine as build

WORKDIR /app

# Bağımlılıkları yükle
COPY package*.json ./
RUN npm ci

# Kaynak kodları kopyala ve derle
COPY . .
RUN npm run build -- --configuration production

# --- Aşama 2: Serve (Sunum) ---
FROM nginx:alpine

# Hazırladığımız Nginx ayarını kopyala
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Angular Build çıktısını Nginx'in sunacağı klasöre kopyala
# NOT: angular.json dosyanızdaki "outputPath" ayarına göre burası '/browser' içerir
COPY --from=build /app/dist/cocktail-analyzer-frontend/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
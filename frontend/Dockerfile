FROM node:20 AS builder
WORKDIR /app

# copy package files to leverage layer caching
COPY package.json package-lock.json tsconfig.json vite.config.ts index.html ./
COPY src ./src

RUN npm ci --no-audit --no-fund && npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Ensure a favicon file is present to avoid 404s from browsers
COPY favicon.ico /usr/share/nginx/html/favicon.ico
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

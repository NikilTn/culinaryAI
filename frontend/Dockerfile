# 1) Build stage: uses your exact Node version
FROM node:20.12.2-alpine AS builder
WORKDIR /usr/src/app
COPY .env .  
COPY package*.json .  
RUN npm ci
COPY . .
RUN npm run build



# 2) Run stage: serve static build
FROM nginx:stable-alpine
COPY --from=builder /usr/src/app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


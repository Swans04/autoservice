# ========================================================
#  ФАЙЛ: frontend/Dockerfile
#  Образ для React-приложения
# ========================================================
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

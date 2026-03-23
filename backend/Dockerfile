# ========================================================
#  ФАЙЛ: backend/Dockerfile
#  Образ для Django-сервера
# ========================================================
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Сначала копируем только requirements.txt (кэширование слоёв Docker)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Создаём директорию для логов
RUN mkdir -p logs media

# Открываем порт 8000
EXPOSE 8000

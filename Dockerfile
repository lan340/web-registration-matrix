FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .
COPY templates/ ./templates/

# Создание директории для данных (база данных)
RUN mkdir -p /app/data

# Порт приложения
EXPOSE 5000

# Переменные окружения по умолчанию
ENV SYNAPSE_ADMIN_URL=http://synapse:8008
ENV MATRIX_SERVER_NAME=localhost
ENV DATABASE_URL=/app/data/codes.db
ENV SECRET_KEY=change-me-in-production

CMD ["python", "app.py"]

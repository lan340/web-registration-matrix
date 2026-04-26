FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .
COPY templates/ ./templates/

# Порт приложения
EXPOSE 5000

# Переменные окружения по умолчанию
ENV SYNAPSE_URL=http://synapse:8008
ENV MATRIX_SERVER_NAME=localhost
ENV FLASK_SECRET_KEY=change-me-in-production

# Запуск через gunicorn для production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]

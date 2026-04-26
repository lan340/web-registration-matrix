# Docker Compose установка панели регистрации Matrix Synapse

Этот документ описывает установку панели регистрации через Docker Compose.

## 📋 Предварительные требования

- Docker и Docker Compose установлены
- Работающий сервер Matrix Synapse
- Доступ к административному интерфейсу Synapse

## 🚀 Быстрый старт

### Шаг 1: Клонирование репозитория

```bash
git clone <ваш-репозиторий>
cd <каталог-репозитория>
```

### Шаг 2: Настройка переменных окружения

Скопируйте шаблон файла окружения:

```bash
cp .env.example .env
```

Откройте `.env` и заполните необходимые значения:

```bash
nano .env
```

**Обязательные параметры:**

| Параметр | Описание | Пример |
|----------|----------|--------|
| `SYNAPSE_ADMIN_URL` | URL вашего Synapse сервера | `http://synapse:8008` или `https://matrix.example.com` |
| `MATRIX_SERVER_NAME` | Домен вашего Matrix сервера | `example.com` |
| `SYNAPSE_ADMIN_ACCESS_TOKEN` | Токен администратора Synapse | `см. ниже как получить` |
| `SECRET_KEY` | Секретный ключ для Flask | Сгенерируйте: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Шаг 3: Получение токена администратора Synapse

#### Способ 1: Через registration_shared_secret (рекомендуется)

1. Откройте конфигурационный файл Synapse `homeserver.yaml`
2. Добавьте или раскомментируйте строку:
   ```yaml
   registration_shared_secret: "ваш-секретный-ключ"
   ```
3. Перезапустите Synapse
4. Получите токен:
   ```bash
   curl -X POST 'http://localhost:8008/_synapse/admin/v1/login' \
     -H 'Content-Type: application/json' \
     -d '{
       "type": "login_token",
       "user": "@admin:example.com",
       "password": "ваш-пароль"
     }'
   ```
5. Скопируйте значение `access_token` из ответа в `.env`

#### Способ 2: Через существующий токен администратора

Если у вас уже есть токен администратора, создайте новый:

```bash
curl -X POST 'http://localhost:8008/_synapse/admin/v1/users/@admin:example.com/login' \
  -H 'Authorization: Bearer <существующий-токен>' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### Шаг 4: Настройка docker-compose.yml

#### Вариант A: Synapse уже запущен в отдельном Docker Compose

Отредактируйте `docker-compose.yml`:

1. Закомментируйте или удалите секцию `synapse:` (строки ~42-60)
2. Измените сеть на ту, где запущен ваш Synapse:
   ```yaml
   networks:
     - имя-вашей-сети-с-synapse
   ```
3. Или используйте внешний адрес в `SYNAPSE_ADMIN_URL`

#### Вариант B: Установка с нуля (Synapse + панель вместе)

Используйте `docker-compose.yml` как есть, заменив значения в `.env`.

### Шаг 5: Запуск

```bash
docker compose up -d --build
```

Проверьте статус:

```bash
docker compose ps
```

Просмотрите логи:

```bash
docker compose logs -f matrix-registration-panel
```

### Шаг 6: Доступ к панели

- **Панель регистрации для пользователей:** `http://localhost:5000/register`
- **Админ-панель:** `http://localhost:5000/admin`

## 🔧 Интеграция с существующим Docker Compose

Если у вас уже есть `docker-compose.yml` с Synapse:

### Опция 1: Добавить сервис в существующий файл

Добавьте секцию `matrix-registration-panel:` в ваш существующий `docker-compose.yml`:

```yaml
services:
  synapse:
    # ... ваша конфигурация ...
  
  matrix-registration-panel:
    build: ./path-to-registration-panel
    container_name: matrix-registration-panel
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - SYNAPSE_ADMIN_URL=http://synapse:8008
      - MATRIX_SERVER_NAME=your-domain.com
      - SYNAPSE_ADMIN_ACCESS_TOKEN=your-token
      - SECRET_KEY=your-secret-key
      - DATABASE_URL=/app/data/codes.db
    volumes:
      - registration-panel-data:/app/data
    networks:
      - ваша-сеть
    depends_on:
      - synapse

volumes:
  registration-panel-data:
```

### Опция 2: Использовать отдельный docker-compose.yml

Создайте `docker-compose.override.yml` или отдельный файл:

```bash
docker compose -f docker-compose.yml -f docker-compose.registration.yml up -d
```

## 🌐 Настройка доступа извне

### Через Nginx (рекомендуется)

Создайте конфигурацию Nginx:

```nginx
server {
    listen 443 ssl;
    server_name register.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### В docker-compose.yml добавьте:

```yaml
networks:
  synapse-network:
    external: true  # Если используете сеть nginx-proxy-manager или similar
```

## 🔒 Безопасность

1. **Смените все пароли и ключи по умолчанию**
2. **Используйте HTTPS** в продакшене
3. **Ограничьте доступ к админ-панели** через firewall или auth
4. **Регулярно обновляйте образы**: `docker compose pull && docker compose up -d`

## 🛠️ Управление

### Просмотр логов

```bash
docker compose logs -f matrix-registration-panel
```

### Перезапуск

```bash
docker compose restart matrix-registration-panel
```

### Остановка

```bash
docker compose down
```

### Обновление

```bash
docker compose pull
docker compose up -d --build
```

### Резервное копирование базы данных

```bash
docker cp matrix-registration-panel:/app/data/codes.db ./backup-codes.db
```

## ❓ Решение проблем

### Панель не подключается к Synapse

1. Проверьте `SYNAPSE_ADMIN_URL` - должен быть доступен из контейнера
2. Убедитесь, что сервисы в одной сети
3. Проверьте логи: `docker compose logs matrix-registration-panel`

### Ошибка аутентификации

1. Проверьте токен администратора
2. Убедитесь, что пользователь имеет права администратора
3. Проверьте `registration_shared_secret` в конфиге Synapse

### Конфликты портов

Измените порт в `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Доступ по порту 8080
```

## 📊 Мониторинг

Проверка здоровья сервиса:

```bash
curl http://localhost:5000/health
```

Статус контейнера:

```bash
docker inspect matrix-registration-panel --format='{{.State.Health.Status}}'
```

## 📝 Дополнительные ресурсы

- [Документация Synapse Admin API](https://matrix-org.github.io/synapse/latest/admin_api/)
- [Официальная регистрация по кодам в Synapse](https://matrix-org.github.io/synapse/latest/registration.html)

# Веб-панель для регистрации в Matrix Synapse по кодам

Веб-приложение для регистрации пользователей в Matrix Synapse с использованием специальных кодов доступа (Registration Tokens).

**Важно:** Это приложение предоставляет только форму регистрации для пользователей. Создание и управление кодами производится через внешнюю админ-панель (например, `synapse-admin`).

## Возможности

- **Простая регистрация** - форма ввода логина, пароля и кода доступа
- **Интеграция с Synapse** - прямая отправка данных в Matrix Synapse через Admin API
- **Валидация кодов** - проверка кода перед регистрацией через Synapse API
- **Docker Compose установка** - готовая конфигурация для развёртывания
- **Лёгковесность** - нет собственной базы данных, вся логика кодов на стороне Synapse

## Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Клонирование репозитория
git clone <ваш-репозиторий>
cd <каталог-репозитория>

# Настройка переменных окружения
cp .env.example .env
nano .env  # Заполните своими значениями

# Запуск
docker compose up -d --build
```

Доступ после запуска:
- Страница регистрации: http://localhost:5000

### Вариант 2: Локальная установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения:
```bash
export SYNAPSE_URL="http://localhost:8008"
export SYNAPSE_ADMIN_ACCESS_TOKEN="ваш_токен_администратора"
export MATRIX_SERVER_NAME="example.com"
export FLASK_SECRET_KEY="случайная-строка-для-сессий"
```

3. Запустите приложение:
```bash
python app.py
```

4. Откройте в браузере:
   - Страница регистрации: http://localhost:5000

## Получение токена администратора Synapse

Для работы приложения нужен токен администратора Matrix Synapse. Получите его через API:

```bash
curl -X POST 'http://localhost:8008/_synapse/admin/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"type": "m.login.password", "identifier": {"user": "admin"}, "password": "ваш_пароль"}'
```

Используйте поле `access_token` из ответа в переменной окружения `SYNAPSE_ADMIN_ACCESS_TOKEN`.

**Альтернативно:** Если вы используете `synapse-admin`, токен можно получить там или создать отдельный токен для этого приложения.

## Настройка Synapse

В конфигурации Synapse (`homeserver.yaml`) должны быть включены:

```yaml
enable_registration: true
registration_requires_token: true
enable_admin_api: true
```

После изменения конфига перезапустите Synapse.

## Создание кодов регистрации

Коды создаются **только через внешнюю админ-панель** (например, `synapse-admin`):

1. Откройте вашу `synapse-admin` панель
2. Перейдите в раздел **Registration Tokens** (или similar)
3. Создайте новый токен:
   - Укажите сам токен (строку) или сгенерируйте
   - Установите лимит использований (сколько раз можно зарегистрироваться)
   - Опционально: срок действия
4. Сохраните и передайте токен пользователю

Приложение не создаёт коды самостоятельно — оно только проверяет их валидность через Synapse API при регистрации.

## Как это работает

1. Пользователь заходит на страницу регистрации `http://ваш-сервер:5000`
2. Вводит желаемый логин, пароль и код доступа (полученный от администратора)
3. Приложение отправляет запрос в Synapse Admin API для регистрации
4. Synapse проверяет код и создаёт пользователя
5. Пользователь может войти в Matrix клиент с новыми учётными данными

## API Endpoints

- `GET /` - страница регистрации
- `POST /api/register` - регистрация пользователя (проверяет код через Synapse)

## Структура проекта

```
├── app.py                      # Основное Flask приложение
├── requirements.txt            # Зависимости Python
├── Dockerfile                  # Docker образ приложения
├── docker-compose.yml          # Конфигурация Docker Compose
├── .env.example                # Шаблон переменных окружения
├── README.md                   # Этот файл
└── templates/
    └── register.html           # Страница регистрации
```

## Файлы для Docker Compose

- **Dockerfile** - образ приложения с Python и зависимостями
- **docker-compose.yml** - конфигурация сервиса панели регистрации
- **.env.example** - шаблон для файла переменных окружения `.env`

## Требования

- Docker и Docker Compose (для контейнерной установки)
- Python 3.8+ (для локальной установки)
- Matrix Synapse с включённым Admin API и регистрацией по токенам
- Внешняя админ-панель (например, `synapse-admin`) для создания кодов

## Интеграция с существующим Docker Compose

Если у вас уже есть `docker-compose.yml` с Synapse и synapse-admin:

1. Добавьте сервис `matrix-register` в ваш существующий файл
2. Убедитесь, что сервис находится в той же сети, что и Synapse
3. Передайте правильные переменные окружения:
   - `SYNAPSE_URL` - внутренний адрес Synapse (например, `http://synapse:8008`)
   - `SYNAPSE_ADMIN_ACCESS_TOKEN` - токен администратора
   - `MATRIX_SERVER_NAME` - домен вашего Matrix сервера
   - `FLASK_SECRET_KEY` - случайная строка для сессий Flask

Пример добавления в существующий `docker-compose.yml`:

```yaml
services:
  # ваши существующие сервисы...
  
  matrix-register:
    build: ./path-to-this-repo
    ports:
      - "5000:5000"
    environment:
      - SYNAPSE_URL=http://synapse:8008
      - SYNAPSE_ADMIN_ACCESS_TOKEN=${SYNAPSE_ADMIN_TOKEN}
      - MATRIX_SERVER_NAME=matrix.example.com
      - FLASK_SECRET_KEY=${FLASK_SECRET}
    networks:
      - your-synapse-network
    restart: unless-stopped
    depends_on:
      - synapse
```

## Безопасность

- Коды проверяются напрямую через Synapse API
- Токен администратора хранится только в переменных окружения
- Для продакшена рекомендуется использовать HTTPS (через reverse proxy)
- Сессионные данные защищаются `FLASK_SECRET_KEY`

## Лицензия

MIT

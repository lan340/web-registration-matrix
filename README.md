# Веб-панель для регистрации в Matrix Synapse по кодам

Веб-приложение для управления регистрацией пользователей в Matrix Synapse с использованием специальных кодов доступа.

## Возможности

- **Генерация кодов регистрации** - создание одноразовых или многократных кодов
- **Настройка срока действия** - указание времени жизни кода
- **Лимит использований** - ограничение количества регистраций на один код
- **Панель администратора** - управление кодами и просмотр логов
- **Страница регистрации** - форма для пользователей с вводом кода
- **Docker Compose установка** - готовая конфигурация для развёртывания в Docker

## Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

Смотрите подробную инструкцию в [DOCKER_COMPOSE_SETUP.md](DOCKER_COMPOSE_SETUP.md)

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
- Панель регистрации: http://localhost:5000/register
- Админ-панель: http://localhost:5000/admin

### Вариант 2: Локальная установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения:
```bash
export SYNAPSE_ADMIN_URL="http://localhost:8008"
export SYNAPSE_ADMIN_ACCESS_TOKEN="ваш_токен_администратора"
export MATRIX_SERVER_NAME="example.com"
```

3. Запустите приложение:
```bash
python app.py
```

4. Откройте в браузере:
   - Страница регистрации: http://localhost:5000/register
   - Панель администратора: http://localhost:5000/admin

## Получение токена администратора Synapse

Для работы приложения нужен токен администратора Matrix Synapse:

```bash
curl -X POST 'http://localhost:8008/_synapse/admin/v1/login' \
  -H 'Content-Type: application/json' \
  -d '{"type": "m.login.password", "identifier": {"user": "admin"}, "password": "ваш_пароль"}'
```

Используйте поле `access_token` из ответа.

## Конфигурация Synapse

В конфигурации Synapse (`homeserver.yaml`) убедитесь, что Admin API доступен:

```yaml
enable_admin_api: true
admin_contact: "mailto:admin@example.com"
```

## API Endpoints

### Публичные
- `POST /api/register` - регистрация пользователя с кодом
- `POST /api/validate-code` - проверка валидности кода

### Административные
- `POST /api/generate-code` - создание нового кода
- `GET /api/codes` - список всех кодов
- `POST /api/deactivate-code/<id>` - деактивация кода
- `GET /api/logs` - логи регистраций

## Структура проекта

```
├── app.py                      # Основное Flask приложение
├── requirements.txt            # Зависимости Python
├── Dockerfile                  # Docker образ приложения
├── docker-compose.yml          # Конфигурация Docker Compose
├── .env.example                # Шаблон переменных окружения
├── DOCKER_COMPOSE_SETUP.md     # Подробная инструкция по Docker Compose
├── README.md                   # Этот файл
├── templates/
│   ├── register.html           # Страница регистрации
│   └── admin.html              # Панель администратора
└── data/                       # Данные (база данных кодов, создаётся автоматически)
```

## Файлы для Docker Compose

- **Dockerfile** - образ приложения с Python и зависимостями
- **docker-compose.yml** - конфигурация сервисов (панель + опционально Synapse)
- **.env.example** - шаблон для файла переменных окружения `.env`
- **DOCKER_COMPOSE_SETUP.md** - детальная документация по установке через Docker

## Требования

- Python 3.8+ (для локальной установки)
- Docker и Docker Compose (для контейнерной установки)
- Matrix Synapse с включённым Admin API
- Доступ к Admin API Synapse

## Безопасность

- Коды генерируются с использованием криптографически стойкого ГСЧ
- Поддержка HTTPS рекомендуется для продакшена
- Токен администратора хранится только в переменных окружения
- Логируются все попытки регистрации

## Лицензия

MIT

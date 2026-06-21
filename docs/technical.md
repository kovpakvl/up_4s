# SecureOffice: техническая документация

## Назначение

SecureOffice состоит из desktop-приложения администратора, Flask backend, PostgreSQL и браузерного кабинета сотрудника. Desktop-приложение запускает серверную часть через Docker Compose, а сотрудники подключаются к web-кабинету по локальной ссылке.

## Архитектура

```text
SecureOfficeAdmin.exe / admin_app.py
└─ ui/                     Desktop UI администратора на CustomTkinter
└─ desktop/                API-клиент, Docker Compose controller, генератор паролей
   └─ docker compose
      ├─ backend           Flask API + web-кабинет
      └─ postgres          PostgreSQL 16
```

Ключевые папки:

- `ui/` — desktop-интерфейс администратора.
- `desktop/` — код, который связывает desktop UI с backend и Docker.
- `backend/secureoffice_backend/` — backend, web-шаблоны, репозитории и сервисы.
- `packaging/` — PyInstaller spec.
- `scripts/` — сборочные скрипты.
- `tests/` — backend-тесты.

## Backend

Backend создаётся в `backend/secureoffice_backend/app.py`. Внутри собираются репозитории, сервисы и маршруты.

Основные слои:

- `routes/` — HTTP API и web-страницы.
- `services/` — бизнес-логика: авторизация, сотрудники, пароли, аудит.
- `repositories/` — SQL-запросы к PostgreSQL.
- `schema.sql` — структура БД.
- `time_utils.py` — единое форматирование времени по МСК.

Основные API-группы:

- `/api/status`, `/api/setup-admin`, `/api/login` — стартовая настройка и вход.
- `/api/admin/employees` — сотрудники.
- `/api/admin/departments` — отделы и должности.
- `/api/admin/password-entries` — записи паролей.
- `/api/admin/audit-events` — журнал событий.
- `/login`, `/activate`, `/cabinet` — web-кабинет сотрудника.

## База Данных

PostgreSQL поднимается через `docker-compose.yml`.

Основные таблицы:

- `users` — администраторы и сотрудники.
- `employees` — карточки сотрудников.
- `departments`, `positions` — структура компании.
- `activation_keys` — ключи первичной активации сотрудников.
- `password_entries` — записи паролей.
- `password_history` — история значений пароля.
- `audit_events` — журнал действий.

Пароли пользователей хешируются PBKDF2. Сохранённые пароли шифруются Fernet-ключом из переменной окружения контейнера.

## Desktop-Приложение

Точка входа: `admin_app.py`.

Desktop UI хранит состояние в `ui/state.py`, работает с backend через `desktop/api_client.py` и запускает сервер через `desktop/server_control.py`.

`ComposeServerController`:

- проверяет наличие Docker;
- проверяет доступность Docker daemon;
- запускает `docker compose up -d --build`;
- использует стабильное имя проекта `secureoffice`;
- в exe берёт compose-файлы из PyInstaller runtime-директории.

## Exe-Сборка

Сборка выполняется командой:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

Скрипт:

1. Создаёт `.venv`, если её нет.
2. Ставит runtime-зависимости из `requirements.txt`.
3. Ставит PyInstaller.
4. Чистит `build/` и `dist/`.
5. Собирает `dist\SecureOfficeAdmin.exe` по `packaging\SecureOfficeAdmin.spec`.

В exe включаются:

- desktop UI;
- backend-код;
- `docker-compose.yml`;
- `backend/Dockerfile`;
- `backend/requirements.txt`.

Docker Desktop не вшивается в exe. На машине администратора он должен быть установлен отдельно. При первом запуске серверной части Docker скачивает образы и собирает backend-контейнер.

## Локальный Запуск

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe admin_app.py
```

Backend отдельно:

```powershell
docker compose up -d --build
```

## Проверки

```powershell
python -m compileall backend\secureoffice_backend ui desktop admin_app.py
python -m pytest
```

Для проверки сборки:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean packaging\SecureOfficeAdmin.spec
```

## Ограничения Учебного Проекта

- HTTP используется без TLS.
- Секреты backend заданы в `docker-compose.yml` для простоты учебного запуска.
- Docker Desktop требуется установить вручную.
- Роли БД и модель прав можно развивать дальше: текущая прикладная модель уже отделяет администратора от сотрудника.

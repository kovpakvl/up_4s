# SecureOffice

Учебный менеджер корпоративных паролей для небольшой локальной сети.

Схема продукта:

- системный администратор запускает desktop-приложение SecureOffice Admin;
- приложение поднимает backend и PostgreSQL через Docker Compose;
- сотрудники заходят в браузерный кабинет по локальной ссылке;
- сотрудник активирует аккаунт личным ключом и видит только свои пароли;
- администратор управляет сотрудниками, отделами, должностями, ключами, паролями и журналом событий.

## Как пользоваться готовой сборкой

1. Установите Docker Desktop и запустите его.
2. Скачайте `SecureOfficeAdmin.exe` со страницы релизов репозитория.
3. Запустите exe.
4. Нажмите `Запустить сервер`.
5. Создайте первый аккаунт администратора.
6. Добавьте отделы, должности и сотрудников.
7. Выдайте сотруднику ссылку активации и ключ.

Backend, web-кабинет и PostgreSQL поднимаются локально. Сотрудникам не нужно ставить desktop-приложение: им нужна только ссылка на веб-кабинет.

## Адреса по умолчанию

- desktop-приложение администратора: `SecureOfficeAdmin.exe`;
- backend: `http://127.0.0.1:8765`;
- вход сотрудника: `http://<ip-администратора>:8765/login`;
- активация сотрудника: `http://<ip-администратора>:8765/activate`.

## Разработка

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe admin_app.py
```

Backend отдельно:

```powershell
docker compose up -d --build
```

Тесты:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Сборка exe

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

Скрипт сам создаёт `.venv`, ставит зависимости и собирает:

```text
dist\SecureOfficeAdmin.exe
```

`build/`, `dist/`, архивы и временные файлы не хранятся в репозитории. Готовый exe нужно публиковать через GitHub Releases.

## Структура

- `admin_app.py` — точка входа нового desktop-приложения администратора.
- `ui/` — CustomTkinter-интерфейс администратора.
- `desktop/` — клиент API, запуск Docker Compose и desktop-утилиты.
- `backend/secureoffice_backend/` — Flask backend, web-кабинет сотрудника, API и PostgreSQL-слой.
- `docker-compose.yml` — PostgreSQL + backend.
- `packaging/` — PyInstaller-spec и настройки упаковки.
- `scripts/` — сервисные скрипты, включая сборку exe.
- `tests/` — backend-тесты.

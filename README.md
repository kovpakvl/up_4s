# SecureOffice

Учебный менеджер корпоративных паролей для небольшой локальной сети.

Системный администратор запускает desktop-приложение, поднимает backend и PostgreSQL через Docker Compose, а сотрудники подключаются к web-кабинету по локальной ссылке.

## Документация

- [Пользовательская инструкция](docs/user-guide.md)
- [Техническая документация](docs/technical.md)
- [Продуктовая документация](docs/product.md)

## Быстрый Старт

1. Установите и запустите Docker Desktop.
2. Запустите `SecureOfficeAdmin.exe`.
3. Нажмите `Запустить сервер`.
4. Создайте первый аккаунт администратора.
5. Добавьте отделы, должности и сотрудников.
6. Выдайте сотрудникам ссылки и ключи активации.

Сотрудникам не нужно устанавливать приложение. Они входят через браузер:

```text
http://<ip-администратора>:8765/login
```

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

## Сборка Exe

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

Результат:

```text
dist\SecureOfficeAdmin.exe
```

Exe включает desktop-приложение и файлы backend для Docker Compose. Docker Desktop устанавливается отдельно.

## Структура

- `admin_app.py` — точка входа desktop-приложения.
- `ui/` — интерфейс администратора.
- `desktop/` — API-клиент, Docker Compose controller и desktop-утилиты.
- `backend/secureoffice_backend/` — Flask backend, API и web-кабинет сотрудника.
- `packaging/` — PyInstaller spec.
- `scripts/` — сборочные скрипты.
- `docs/` — документация.
- `tests/` — тесты.

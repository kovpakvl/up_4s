# SecureOffice backend

Новый серверный слой для схемы "админское desktop-ПО + web-кабинет сотрудника".

## Локальный запуск через Docker Compose

```powershell
docker compose up -d --build
```

После запуска API доступен по адресу:

```text
http://127.0.0.1:8765
```

Первичная проверка:

```powershell
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/api/status
```

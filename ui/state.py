"""Глобальное состояние админского приложения.

Хранит API-клиент, сведения о текущем пользователе, кеш отделов/сотрудников
и список наблюдателей. Страницы подписываются на изменения и обновляются
автоматически.
"""
from __future__ import annotations

from typing import Callable, Optional

from desktop.api_client import AdminApiClient, AdminApiError
from desktop.server_control import ComposeServerController, local_server_url


class AppState:
    def __init__(self):
        self.api: AdminApiClient = AdminApiClient("http://127.0.0.1:8765")
        self.server = ComposeServerController()
        self.user: dict = {}
        self.server_url: str = "http://127.0.0.1:8765"
        self.lan_url: str = local_server_url()
        self.activation_url: str = ""
        self.login_url: str = ""
        self.server_online: bool = False
        self.admin_initialized: bool = False
        self._listeners: list[Callable[[], None]] = []
        self._tasks_done: set[str] = set()

    # подписки
    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        def detach() -> None:
            try:
                self._listeners.remove(listener)
            except ValueError:
                pass

        return detach

    def notify(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                pass

    # urls
    def update_urls(self) -> None:
        host = self.lan_url.rstrip("/")
        self.activation_url = f"{host}/activate"
        self.login_url = f"{host}/login"

    # server status
    def refresh_status(self) -> Optional[str]:
        """Возвращает None при успехе, текст ошибки иначе."""
        try:
            payload = self.api.status()
        except AdminApiError as exc:
            self.server_online = False
            self.notify()
            return str(exc)
        self.server_online = True
        self.admin_initialized = bool(payload.get("initialized"))
        self.notify()
        return None

    # auth
    def login(self, username: str, password: str) -> None:
        user = self.api.login(username, password)
        self.user = user
        self.notify()

    def logout(self) -> None:
        self.api.token = ""
        self.api.user = {}
        self.user = {}
        self.notify()

    # onboarding checklist
    def mark_done(self, step: str) -> None:
        self._tasks_done.add(step)
        self.notify()

    def is_done(self, step: str) -> bool:
        return step in self._tasks_done

    @property
    def authorized(self) -> bool:
        return bool(self.user)

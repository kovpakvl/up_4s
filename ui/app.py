"""Корневое приложение SecureOffice Admin на CustomTkinter."""
from __future__ import annotations

import threading
from typing import Optional

import customtkinter as ctk

from admin_api_client import AdminApiError
from admin_server_control import ServerCommandError

from . import theme
from .splash import Splash
from .state import AppState
from .widgets.sidebar import NavItem, Sidebar
from .widgets.toast import ToastManager
from .widgets.topbar import Topbar
from .pages.base import Page
from .pages.placeholder import PlaceholderPage


class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        theme.init("dark")
        self.title("SecureOffice — Admin Console")
        self.geometry("1360x820")
        self.minsize(1180, 720)
        self.configure(fg_color=theme.palette_pair("bg"))

        self.state_obj = AppState()
        self.toasts = ToastManager(self)
        self._pages: dict[str, Page] = {}
        self._current_page_key: Optional[str] = None

        # placeholder shell, реальный рендер — после splash
        self._shell: Optional[ctk.CTkFrame] = None
        self._auth_screen: Optional[ctk.CTkFrame] = None
        self._sidebar: Optional[Sidebar] = None
        self._topbar: Optional[Topbar] = None
        self._content_holder: Optional[ctk.CTkFrame] = None

        self.withdraw()
        self.after(50, self._launch_splash)

        theme.on_theme_change(self._on_theme_changed)
        self.state_obj.subscribe(self._on_state_changed)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── startup ────────────────────────────────────────────────────────
    def _launch_splash(self) -> None:
        Splash(self, self.state_obj, on_done=self._after_splash)

    def _after_splash(self) -> None:
        self.deiconify()
        self._build_shell()
        self._refresh_route()

    # ─── shell ──────────────────────────────────────────────────────────
    def _build_shell(self) -> None:
        if self._shell is not None:
            return
        shell = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        shell.pack(fill="both", expand=True)
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(2, weight=1)

        self._sidebar = Sidebar(shell, on_toggle_theme=self._toggle_theme)
        self._sidebar.grid(row=0, column=0, sticky="ns")
        # тонкая разделительная линия
        sep = ctk.CTkFrame(shell, width=1, fg_color=theme.palette_pair("line"))
        sep.grid(row=0, column=1, sticky="ns")
        sep.grid_propagate(False)

        right = ctk.CTkFrame(shell, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._topbar = Topbar(
            right,
            on_help=self._show_help,
            on_logout=self._logout,
        )
        self._topbar.grid(row=0, column=0, sticky="ew")

        self._content_holder = ctk.CTkFrame(
            right,
            fg_color=theme.palette_pair("bg"),
            corner_radius=0,
        )
        self._content_holder.grid(row=1, column=0, sticky="nsew")
        self._content_holder.grid_columnconfigure(0, weight=1)
        self._content_holder.grid_rowconfigure(0, weight=1)

        self._shell = shell

    def _ensure_pages(self) -> None:
        if self._pages:
            return
        assert self._content_holder is not None
        # импортируем здесь, чтобы избежать циклов и долгого импорта на старте
        from .pages.dashboard import DashboardPage
        from .pages.audit import AuditPage
        from .pages.settings import SettingsPage

        page_specs = [
            ("dashboard", DashboardPage, NavItem("dashboard", "Дашборд", "grid", lambda: self.show_page("dashboard"))),
            ("audit", AuditPage, NavItem("audit", "Журнал", "activity", lambda: self.show_page("audit"))),
            ("settings", SettingsPage, NavItem("settings", "Настройки", "gear", lambda: self.show_page("settings"))),
        ]
        assert self._sidebar is not None
        for key, page_cls, nav in page_specs:
            page = page_cls(self._content_holder, self)
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()
            self._pages[key] = page
            self._sidebar.add_item(nav)

    # ─── routing ────────────────────────────────────────────────────────
    def _refresh_route(self) -> None:
        if not self.state_obj.server_online:
            self._show_auth(offline=True)
            return
        if not self.state_obj.authorized:
            self._show_auth(offline=False)
            return
        self._show_workspace()

    def _show_auth(self, *, offline: bool) -> None:
        self._destroy_auth_screen()
        if self._content_holder is not None:
            self._content_holder.grid_remove()
        if self._sidebar is not None:
            self._sidebar.grid_remove()
        if self._topbar is not None:
            self._topbar.grid_remove()
        from .pages.auth import AuthScreen

        # на время авторизации даём auth-экрану всю ширину
        self._shell.grid_columnconfigure(0, weight=1)
        self._auth_screen = AuthScreen(self._shell, self, offline=offline)
        self._auth_screen.grid(row=0, column=0, columnspan=3, sticky="nsew")

    def _show_workspace(self) -> None:
        self._destroy_auth_screen()
        self._ensure_pages()
        # вернём sidebar колонку как 0-weight, чтобы контент занимал всё свободное место
        self._shell.grid_columnconfigure(0, weight=0)
        if self._sidebar is not None:
            self._sidebar.grid()
        if self._topbar is not None:
            self._topbar.grid()
            self._topbar.set_status(online=self.state_obj.server_online)
            self._topbar.set_user(self.state_obj.user.get("display_name", ""))
        if self._content_holder is not None:
            self._content_holder.grid()
        if self._current_page_key is None:
            self.show_page("dashboard")
        else:
            self.show_page(self._current_page_key)

    def _destroy_auth_screen(self) -> None:
        if self._auth_screen is not None:
            try:
                self._auth_screen.destroy()
            except Exception:
                pass
            self._auth_screen = None

    def show_page(self, key: str) -> None:
        if key not in self._pages:
            return
        for k, page in self._pages.items():
            if k == key:
                page.grid()
                page.tkraise()
                self._current_page_key = key
                if self._topbar is not None:
                    self._topbar.set_title(page.title, page.subtitle)
                page.on_enter()
            else:
                page.grid_remove()
        if self._sidebar is not None:
            self._sidebar.set_active(key)

    # ─── actions ────────────────────────────────────────────────────────
    def _toggle_theme(self) -> None:
        theme.toggle_theme()

    def _on_theme_changed(self, _palette) -> None:
        # перестроим шелл, потому что многие виджеты CTk не реагируют на смену темы во время работы
        try:
            self.configure(fg_color=theme.palette_pair("bg"))
        except Exception:
            pass
        if self._sidebar:
            self._sidebar.update_theme_button()
        # перерисуем активную страницу
        if self._current_page_key:
            self.show_page(self._current_page_key)

    def _on_state_changed(self) -> None:
        if self._topbar is not None and self.state_obj.authorized:
            self._topbar.set_status(online=self.state_obj.server_online)
            self._topbar.set_user(self.state_obj.user.get("display_name", ""))

    def _show_help(self) -> None:
        from .dialogs.onboarding import start_onboarding
        start_onboarding(self)

    def _logout(self) -> None:
        self.state_obj.logout()
        self.toasts.show("Сессия завершена", tone="neutral")
        self._refresh_route()

    def _on_close(self) -> None:
        self.destroy()

    # ─── server control helpers ─────────────────────────────────────────
    def start_server_async(self, on_done) -> None:
        def worker() -> None:
            try:
                output = self.state_obj.server.start()
                error = None
            except ServerCommandError as exc:
                output = ""
                error = str(exc)
            self.after(0, lambda: on_done(output, error))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_status_async(self, on_done=None) -> None:
        def worker() -> None:
            error = self.state_obj.refresh_status()
            self.after(0, lambda: on_done(error) if on_done else None)

        threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    AdminApp().mainloop()

"""Главная страница SecureOffice: hub с верхними вкладками.

В сайдбаре только три раздела: Дашборд, Журнал, Настройки.
Сотрудники / Структура / Пароли — это вкладки внутри Дашборда.
"""
from __future__ import annotations

import customtkinter as ctk

from .. import theme
from ..widgets.empty_state import EmptyState
from ..widgets.tabs import TabSpec, TopTabs
from .base import Page


class DashboardPage(Page):
    title = "Дашборд"
    subtitle = "Главная панель администратора SecureOffice"

    def __init__(self, master, app):
        super().__init__(master, app)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        self.tabs = TopTabs(container, on_change=self._on_tab_change)
        self.tabs.pack(fill="both", expand=True)

        overview = self.tabs.add_tab(TabSpec("overview", "Обзор", "grid", self._build_overview))
        employees = self.tabs.add_tab(TabSpec("employees", "Сотрудники", "users", self._build_employees))
        structure = self.tabs.add_tab(TabSpec("structure", "Структура", "building", self._build_structure))
        passwords = self.tabs.add_tab(TabSpec("passwords", "Пароли", "key", self._build_passwords))

        self.tabs.activate("overview")

    def on_enter(self) -> None:
        # будем перестраивать "Обзор" каждый раз при заходе на дашборд
        pass

    def _on_tab_change(self, key: str) -> None:
        labels = {
            "overview": ("Обзор", "Что требует внимания и сводка по компании"),
            "employees": ("Сотрудники", "Управление людьми и доступами"),
            "structure": ("Структура", "Отделы и должности компании"),
            "passwords": ("Пароли", "Корпоративные учётные записи"),
        }
        title, subtitle = labels.get(key, ("Дашборд", ""))
        if self.app._topbar is not None:
            self.app._topbar.set_title(title, subtitle)

    # ─── вкладки ────────────────────────────────────────────────────────
    def _build_overview(self, parent: ctk.CTkFrame) -> None:
        from .overview import OverviewTab
        self.overview = OverviewTab(parent, self.app)
        self.overview.pack(fill="both", expand=True)

    def _build_employees(self, parent: ctk.CTkFrame) -> None:
        from .employees import build_employees_tab
        build_employees_tab(parent, self.app)

    def _build_structure(self, parent: ctk.CTkFrame) -> None:
        from .structure import build_structure_tab
        build_structure_tab(parent, self.app)

    def _build_passwords(self, parent: ctk.CTkFrame) -> None:
        from .passwords import build_passwords_tab
        build_passwords_tab(parent, self.app)

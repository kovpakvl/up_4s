"""Базовый класс страницы.

ВНИМАНИЕ: Page — обычный CTkFrame, НЕ scrollable. Скролл должен делать
один внутренний контейнер (timeline, list_holder), иначе вложенные
ScrollableFrame обрезают друг другу высоту и контент «съедается».
"""
from __future__ import annotations

import customtkinter as ctk


class Page(ctk.CTkFrame):
    title: str = ""
    subtitle: str = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.app = app

    def on_enter(self) -> None:
        """Вызывается, когда страница становится активной."""

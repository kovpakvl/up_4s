"""Splash-экран при запуске: показывает анимированный логотип и
прогресс проверки сервера.
"""
from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk

from . import theme
from .assets.icons import icon as load_icon
from .state import AppState


class Splash(ctk.CTkToplevel):
    def __init__(self, master, state: AppState, on_done: Callable[[], None]):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=theme.palette_pair("bg"))
        self._state = state
        self._on_done = on_done

        width, height = 460, 240
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        card = ctk.CTkFrame(
            self,
            corner_radius=theme.RADIUS.lg,
            fg_color=theme.palette_pair("surface"),
            border_color=theme.palette_pair("line"),
            border_width=1,
        )
        card.pack(expand=True, fill="both", padx=18, pady=18)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(pady=(28, 8))
        ctk.CTkLabel(
            head,
            text="",
            image=load_icon("shield", 40, "primary"),
            fg_color="transparent",
        ).pack(side="left", padx=(0, 12))
        text_block = ctk.CTkFrame(head, fg_color="transparent")
        text_block.pack(side="left")
        ctk.CTkLabel(
            text_block,
            text="SecureOffice",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_block,
            text="Менеджер корпоративных доступов",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(anchor="w")

        self.status = ctk.CTkLabel(
            card,
            text="Подключаюсь к серверу…",
            text_color=theme.palette_pair("text_soft"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.status.pack(pady=(20, 12))

        self.progress = ctk.CTkProgressBar(
            card,
            width=320,
            height=6,
            corner_radius=3,
            mode="indeterminate",
            progress_color=theme.palette_pair("primary"),
            fg_color=theme.palette_pair("surface_hi"),
        )
        self.progress.pack(pady=(0, 24))
        self.progress.start()

        self.after(150, self._begin_check)

    def _begin_check(self) -> None:
        def worker() -> None:
            error = self._state.refresh_status()
            self.after(0, lambda: self._finish(error))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, error) -> None:
        self.progress.stop()
        if error is None:
            self.status.configure(text="Сервер на связи. Открываю приложение…")
        else:
            self.status.configure(
                text="Сервер не отвечает — продолжу в офлайн-режиме."
            )
        self.after(400, self._close)

    def _close(self) -> None:
        try:
            self.destroy()
        except Exception:
            pass
        self._on_done()

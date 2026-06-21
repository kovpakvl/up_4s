"""Верхняя панель с заголовком страницы, статусом сервера и профилем."""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon
from .avatar import Avatar
from .button import IconButton


class Topbar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        on_help: Optional[Callable[[], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            master,
            corner_radius=0,
            fg_color=theme.color_pair(theme.LIGHT.surface, theme.DARK.surface),
            border_width=0,
            height=70,
        )
        self.pack_propagate(False)
        # тонкая линия снизу — через дочерний фрейм
        line = ctk.CTkFrame(
            self,
            height=1,
            fg_color=theme.palette_pair("line"),
            corner_radius=0,
        )
        line.pack(side="bottom", fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.grid_columnconfigure(1, weight=1)

        # заголовок
        title_block = ctk.CTkFrame(body, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w", pady=14)
        self.title_label = ctk.CTkLabel(
            title_block,
            text="",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text="",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.subtitle_label.pack(anchor="w")

        # правый блок: статус, помощь, выход
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", pady=14)

        self.status_chip = ctk.CTkFrame(
            right,
            corner_radius=theme.RADIUS.pill,
            fg_color=theme.palette_pair("surface_soft"),
        )
        self.status_chip.pack(side="left", padx=(0, 12))
        self.status_dot = ctk.CTkLabel(
            self.status_chip,
            text="●",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
        )
        self.status_dot.pack(side="left", padx=(12, 6), pady=6)
        self.status_text = ctk.CTkLabel(
            self.status_chip,
            text="Проверяю сервер",
            text_color=theme.palette_pair("text_soft"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent",
        )
        self.status_text.pack(side="left", padx=(0, 14), pady=6)

        if on_help:
            IconButton(right, icon="help", tooltip="Подсказки", command=on_help).pack(
                side="left", padx=4
            )
        self._profile = ctk.CTkFrame(right, fg_color="transparent")
        self._profile.pack(side="left", padx=(8, 0))
        self.avatar_holder = ctk.CTkFrame(self._profile, fg_color="transparent")
        self.avatar_holder.pack(side="left")
        self.profile_name = ctk.CTkLabel(
            self._profile,
            text="",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="transparent",
        )
        self.profile_name.pack(side="left", padx=(10, 6))
        if on_logout:
            IconButton(
                right, icon="logout", tooltip="Выйти", command=on_logout
            ).pack(side="left", padx=(8, 0))

        self._avatar_widget: Optional[Avatar] = None

    def set_title(self, title: str, subtitle: str = "") -> None:
        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)

    def set_status(self, *, online: bool, message: str = "") -> None:
        if online:
            self.status_dot.configure(text_color=theme.palette_pair("success"))
            self.status_text.configure(
                text=message or "Сервер на связи",
                text_color=theme.palette_pair("success"),
            )
        else:
            self.status_dot.configure(text_color=theme.palette_pair("danger"))
            self.status_text.configure(
                text=message or "Сервер не отвечает",
                text_color=theme.palette_pair("danger"),
            )

    def set_user(self, display_name: str) -> None:
        self.profile_name.configure(text=display_name or "Гость")
        for child in self.avatar_holder.winfo_children():
            child.destroy()
        if display_name:
            self._avatar_widget = Avatar(self.avatar_holder, display_name, size=32)
            self._avatar_widget.pack()

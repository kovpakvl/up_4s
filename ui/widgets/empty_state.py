"""Пустые состояния для списков и таблиц."""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon
from .button import PrimaryButton


class EmptyState(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        icon: str = "sparkles",
        title: str = "Пока пусто",
        description: str = "",
        action_text: str = "",
        action_command: Optional[Callable] = None,
        **kwargs,
    ):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=theme.SPACING.lg, pady=theme.SPACING.xl)
        inner.grid_columnconfigure(0, weight=1)

        bubble = ctk.CTkFrame(
            inner,
            width=72,
            height=72,
            corner_radius=36,
            fg_color=theme.palette_pair("primary_soft"),
        )
        bubble.grid(row=0, column=0, pady=(0, theme.SPACING.md))
        bubble.grid_propagate(False)
        bubble.grid_rowconfigure(0, weight=1)
        bubble.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            bubble,
            text="",
            image=load_icon(icon, 32, "primary"),
            fg_color="transparent",
        ).grid(row=0, column=0)

        ctk.CTkLabel(
            inner,
            text=title,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            fg_color="transparent",
        ).grid(row=1, column=0, pady=(0, theme.SPACING.xs))

        if description:
            ctk.CTkLabel(
                inner,
                text=description,
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color="transparent",
                wraplength=420,
                justify="center",
            ).grid(row=2, column=0, pady=(0, theme.SPACING.lg))

        if action_text and action_command:
            PrimaryButton(
                inner,
                text=action_text,
                command=action_command,
                icon="plus",
            ).grid(row=3, column=0)

"""Карточка с метрикой: иконка, число, подпись, опциональный тренд."""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon


class StatCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        icon: str,
        label: str,
        value: str = "—",
        tone: str = "primary",
        hint: str = "",
        **kwargs,
    ):
        kwargs.setdefault("corner_radius", theme.RADIUS.lg)
        kwargs.setdefault("fg_color", theme.palette_pair("surface"))
        kwargs.setdefault("border_color", theme.palette_pair("line"))
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)
        bg_attr = f"{tone}_soft" if tone in {"primary", "success", "warning", "danger", "info"} else "surface_hi"

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(16, 4))
        bubble = ctk.CTkFrame(
            head,
            width=38,
            height=38,
            corner_radius=12,
            fg_color=theme.palette_pair(bg_attr),
        )
        bubble.pack(side="left")
        bubble.pack_propagate(False)
        ctk.CTkLabel(
            bubble,
            text="",
            image=load_icon(icon, 20, tone),
            fg_color="transparent",
        ).pack(expand=True)
        ctk.CTkLabel(
            head,
            text=label,
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent",
        ).pack(side="left", padx=(12, 0))

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            fg_color="transparent",
            anchor="w",
        )
        self.value_label.pack(fill="x", padx=18, pady=(2, 4))

        self.hint_label = ctk.CTkLabel(
            self,
            text=hint or " ",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            anchor="w",
        )
        self.hint_label.pack(fill="x", padx=18, pady=(0, 14))

    def set_value(self, value: str, hint: Optional[str] = None) -> None:
        self.value_label.configure(text=value)
        if hint is not None:
            self.hint_label.configure(text=hint or " ")

"""Диалог истории изменений пароля."""
from __future__ import annotations

import customtkinter as ctk

from .. import theme
from ..time_utils import format_moscow_datetime
from ..widgets.button import PrimaryButton
from .base_dialog import Dialog


def show_password_history(app, *, entry: dict, history: list[dict]) -> None:
    dialog = Dialog(
        app,
        title=f"История · {entry.get('service_name', '')}",
        width=540,
        height=460,
    )
    if not history:
        ctk.CTkLabel(
            dialog.body,
            text="Истории изменений пока нет — этот пароль ещё не менялся.",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
        ).pack(anchor="w")
    else:
        scroll = ctk.CTkScrollableFrame(
            dialog.body,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        scroll.pack(fill="both", expand=True)
        for item in history:
            row = ctk.CTkFrame(
                scroll,
                fg_color=theme.palette_pair("surface_soft"),
                corner_radius=theme.RADIUS.md,
            )
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)
            ctk.CTkLabel(
                inner,
                text=format_moscow_datetime(item.get("created_at", "")),
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color="transparent",
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                inner,
                text=item.get("password", "—") or "—",
                text_color=theme.palette_pair("text"),
                font=ctk.CTkFont(family="Consolas", size=13),
                fg_color="transparent",
            ).pack(side="right")
    PrimaryButton(
        dialog.footer, text="Закрыть", icon="check", command=dialog.destroy
    ).pack(side="right")

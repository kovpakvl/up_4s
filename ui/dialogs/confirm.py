"""Confirm-диалог в стиле SecureOffice."""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.button import DangerButton, PrimaryButton, SecondaryButton
from .base_dialog import Dialog


def confirm(
    master,
    *,
    title: str,
    message: str,
    confirm_text: str = "Подтвердить",
    cancel_text: str = "Отмена",
    tone: str = "primary",
    icon: str = "alert",
    on_confirm: Optional[Callable[[], None]] = None,
) -> None:
    dialog = Dialog(master, title=title, width=460, height=260)

    bubble = ctk.CTkFrame(
        dialog.body,
        width=52,
        height=52,
        corner_radius=18,
        fg_color=theme.palette_pair(f"{tone}_soft"),
    )
    bubble.pack(anchor="w")
    bubble.pack_propagate(False)
    ctk.CTkLabel(
        bubble,
        text="",
        image=load_icon(icon, 24, tone),
        fg_color="transparent",
    ).pack(expand=True)
    ctk.CTkLabel(
        dialog.body,
        text=message,
        text_color=theme.palette_pair("text_soft"),
        font=ctk.CTkFont(family="Segoe UI", size=13),
        fg_color="transparent",
        wraplength=400,
        justify="left",
        anchor="w",
    ).pack(fill="x", anchor="w", pady=(14, 0))

    btn_class = DangerButton if tone == "danger" else PrimaryButton

    def go() -> None:
        dialog.destroy()
        if on_confirm:
            on_confirm()

    btn_class(dialog.footer, text=confirm_text, command=go).pack(side="right")
    SecondaryButton(
        dialog.footer, text=cancel_text, command=dialog.destroy
    ).pack(side="right", padx=(0, 8))

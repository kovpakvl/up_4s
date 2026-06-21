"""Диалог выдачи ключа активации сотруднику.

После создания сотрудника или повторной выдачи ключа мы показываем:
- большой код,
- QR-код,
- ссылку для активации,
- три кнопки: «Скопировать инструкцию», «Скопировать ключ», «Скопировать ссылку».
"""
from __future__ import annotations

import io
from typing import Optional

import customtkinter as ctk
import qrcode
from PIL import Image

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.button import PrimaryButton, SecondaryButton
from ..widgets.card import GhostCard, OutlineCard
from .base_dialog import Dialog


def _make_qr_image(text: str, size: int = 200) -> ctk.CTkImage:
    qr = qrcode.QRCode(border=1, box_size=8)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def show_activation_key(
    app,
    *,
    employee: dict,
    code: str,
    expires_at: str,
    activation_url: str,
) -> None:
    dialog = Dialog(
        app,
        title="Ключ активации сотрудника",
        width=620,
        height=540,
    )

    intro = ctk.CTkLabel(
        dialog.body,
        text=f"Передайте код сотруднику {employee.get('full_name', '')}",
        text_color=theme.palette_pair("text_soft"),
        font=ctk.CTkFont(family="Segoe UI", size=13),
        fg_color="transparent",
        anchor="w",
    )
    intro.pack(fill="x", anchor="w")

    body = ctk.CTkFrame(dialog.body, fg_color="transparent")
    body.pack(fill="both", expand=True, pady=(14, 0))
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=0)

    # левая колонка: код, ссылка, срок
    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))

    code_card = OutlineCard(left)
    code_card.pack(fill="x")
    ctk.CTkLabel(
        code_card,
        text="Код активации",
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color="transparent",
    ).pack(anchor="w", padx=18, pady=(14, 2))
    ctk.CTkLabel(
        code_card,
        text=code,
        text_color=theme.palette_pair("primary"),
        font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
        fg_color="transparent",
    ).pack(anchor="w", padx=18, pady=(0, 14))

    url_card = OutlineCard(left)
    url_card.pack(fill="x", pady=(12, 0))
    ctk.CTkLabel(
        url_card,
        text="Ссылка для активации",
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color="transparent",
    ).pack(anchor="w", padx=18, pady=(14, 2))
    ctk.CTkLabel(
        url_card,
        text=activation_url,
        text_color=theme.palette_pair("text"),
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color="transparent",
        wraplength=300,
        justify="left",
        anchor="w",
    ).pack(fill="x", anchor="w", padx=18, pady=(0, 14))

    expires = ctk.CTkLabel(
        left,
        text=f"Действует до: {expires_at}",
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=11),
        fg_color="transparent",
        anchor="w",
    )
    expires.pack(fill="x", anchor="w", pady=(12, 0))

    # правая колонка: QR
    right = GhostCard(body)
    right.grid(row=0, column=1, sticky="ns")
    qr_label = ctk.CTkLabel(
        right,
        text="",
        image=_make_qr_image(f"{activation_url}?code={code}"),
        fg_color="transparent",
    )
    qr_label.pack(padx=18, pady=18)
    ctk.CTkLabel(
        right,
        text="Отсканируйте\nс телефона",
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=11),
        fg_color="transparent",
        justify="center",
    ).pack(pady=(0, 18))

    # футер: действия
    def copy_code() -> None:
        app.clipboard_clear()
        app.clipboard_append(code)
        app.toasts.show("Код активации скопирован", tone="success")

    def copy_link() -> None:
        app.clipboard_clear()
        app.clipboard_append(f"{activation_url}?code={code}")
        app.toasts.show("Ссылка с кодом скопирована", tone="success")

    def copy_instruction() -> None:
        text = (
            f"Здравствуйте, {employee.get('full_name', '')}!\n"
            f"Активируйте свой доступ в SecureOffice:\n"
            f"• Ссылка: {activation_url}\n"
            f"• Код: {code}\n"
            f"• Действует до: {expires_at}\n"
        )
        app.clipboard_clear()
        app.clipboard_append(text)
        app.toasts.show("Готовое сообщение в буфере обмена", tone="success")

    PrimaryButton(
        dialog.footer,
        text="Готово",
        icon="check",
        command=dialog.destroy,
    ).pack(side="right")
    SecondaryButton(
        dialog.footer,
        text="Скопировать ссылку",
        icon="copy",
        command=copy_link,
    ).pack(side="right", padx=(0, 8))
    SecondaryButton(
        dialog.footer,
        text="Скопировать код",
        icon="key",
        command=copy_code,
    ).pack(side="right", padx=(0, 8))
    SecondaryButton(
        dialog.footer,
        text="Скопировать инструкцию",
        icon="mail",
        command=copy_instruction,
    ).pack(side="right", padx=(0, 8))

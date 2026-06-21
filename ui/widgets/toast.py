"""Toast-уведомления в правом нижнем углу окна.

Каждое уведомление — отдельный CTkFrame, который сам себя позиционирует
и анимирует появление/уход.
"""
from __future__ import annotations

from typing import Literal, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon


Tone = Literal["success", "warning", "danger", "info", "neutral"]


_TONE_ICONS = {
    "success": ("check", "success"),
    "warning": ("alert", "warning"),
    "danger": ("alert", "danger"),
    "info": ("activity", "info"),
    "neutral": ("activity", "text_soft"),
}


class _ToastItem(ctk.CTkFrame):
    def __init__(
        self,
        master,
        text: str,
        tone: Tone,
        on_close,
    ):
        super().__init__(
            master,
            corner_radius=theme.RADIUS.md,
            fg_color=theme.palette_pair("surface"),
            border_color=theme.palette_pair("line"),
            border_width=1,
        )
        icon_name, tone_attr = _TONE_ICONS.get(tone, _TONE_ICONS["neutral"])
        icon_label = ctk.CTkLabel(
            self,
            text="",
            image=load_icon(icon_name, 20, tone_attr),
            fg_color="transparent",
        )
        icon_label.grid(row=0, column=0, padx=(14, 10), pady=12)
        text_label = ctk.CTkLabel(
            self,
            text=text,
            text_color=theme.palette_pair("text"),
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            justify="left",
            anchor="w",
            wraplength=280,
        )
        text_label.grid(row=0, column=1, sticky="w", pady=12)
        close = ctk.CTkButton(
            self,
            text="",
            image=load_icon("close", 14, "text_muted"),
            width=28,
            height=28,
            corner_radius=theme.RADIUS.sm,
            fg_color="transparent",
            hover_color=theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
            command=on_close,
        )
        close.grid(row=0, column=2, padx=(8, 8))


class ToastManager:
    def __init__(self, root: ctk.CTk):
        self._root = root
        self._stack: list[_ToastItem] = []

    def show(
        self,
        text: str,
        tone: Tone = "neutral",
        *,
        duration_ms: int = 3800,
    ) -> None:
        item = _ToastItem(self._root, text, tone, on_close=lambda: self._dismiss(item))
        self._stack.append(item)
        self._reflow()
        if duration_ms > 0:
            self._root.after(duration_ms, lambda: self._dismiss(item))

    def _dismiss(self, item: _ToastItem) -> None:
        if item not in self._stack:
            return
        self._stack.remove(item)
        try:
            item.place_forget()
            item.destroy()
        except Exception:
            pass
        self._reflow()

    def _reflow(self) -> None:
        if not self._stack:
            return
        self._root.update_idletasks()
        root_h = self._root.winfo_height()
        y = root_h - 24
        for item in reversed(self._stack):
            item.update_idletasks()
            h = item.winfo_reqheight()
            y -= h + 10
            item.place(
                relx=1.0,
                x=-24,
                y=y,
                anchor="ne",
            )
            item.lift()

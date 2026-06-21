"""Бэйдж — компактная плашка статуса."""
from __future__ import annotations

import customtkinter as ctk

from .. import theme


_TONES = {
    "neutral": ("surface_hi", "text_soft"),
    "primary": ("primary_soft", "primary"),
    "success": ("success_soft", "success"),
    "warning": ("warning_soft", "warning"),
    "danger": ("danger_soft", "danger"),
    "info": ("info_soft", "info"),
}


class Badge(ctk.CTkLabel):
    def __init__(self, master, text: str, *, tone: str = "neutral", **kwargs):
        bg_attr, fg_attr = _TONES.get(tone, _TONES["neutral"])
        kwargs.setdefault("corner_radius", theme.RADIUS.pill)
        kwargs.setdefault("fg_color", theme.palette_pair(bg_attr))
        kwargs.setdefault("text_color", theme.palette_pair(fg_attr))
        kwargs.setdefault(
            "font", ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        kwargs.setdefault("padx", 10)
        kwargs.setdefault("pady", 3)
        super().__init__(master, text=text, **kwargs)

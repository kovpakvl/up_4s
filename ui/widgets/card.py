"""Карточки — основные контейнеры контента."""
from __future__ import annotations

import customtkinter as ctk

from .. import theme


class Card(ctk.CTkFrame):
    """Карточка с заливкой surface и скруглением."""

    def __init__(self, master, *, padding: int = theme.SPACING.lg, **kwargs):
        kwargs.setdefault("corner_radius", theme.RADIUS.lg)
        kwargs.setdefault(
            "fg_color",
            theme.palette_pair("surface"),
        )
        kwargs.setdefault(
            "border_color",
            theme.palette_pair("line"),
        )
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)
        if padding:
            self._inner_padding = padding


class GhostCard(ctk.CTkFrame):
    """Полупрозрачная карточка для блоков на цветном фоне (sidebar/hero)."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", theme.RADIUS.md)
        kwargs.setdefault(
            "fg_color",
            theme.palette_pair("surface_soft"),
        )
        kwargs.setdefault("border_width", 0)
        super().__init__(master, **kwargs)


class OutlineCard(ctk.CTkFrame):
    """Прозрачная карточка только с обводкой."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", theme.RADIUS.md)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault(
            "border_color",
            theme.palette_pair("line"),
        )
        kwargs.setdefault("border_width", 1)
        super().__init__(master, **kwargs)

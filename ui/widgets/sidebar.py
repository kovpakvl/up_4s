"""Боковая навигация со сворачиванием и иконками."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon


@dataclass
class NavItem:
    key: str
    title: str
    icon: str
    command: Callable[[], None]


class Sidebar(ctk.CTkFrame):
    EXPANDED_WIDTH = 232
    COLLAPSED_WIDTH = 76

    def __init__(self, master, *, on_toggle_theme: Callable[[], None]):
        super().__init__(
            master,
            corner_radius=0,
            fg_color=theme.color_pair(theme.LIGHT.surface, theme.DARK.surface),
            border_width=0,
            width=self.EXPANDED_WIDTH,
        )
        self.pack_propagate(False)
        self._expanded = True
        self._on_toggle_theme = on_toggle_theme
        self._items: dict[str, dict] = {}
        self._active: Optional[str] = None

        self._brand = ctk.CTkFrame(self, fg_color="transparent")
        self._brand.pack(fill="x", pady=(18, 18), padx=14)
        self._brand_icon = ctk.CTkLabel(
            self._brand,
            text="",
            image=load_icon("shield", 26, "primary"),
            fg_color="transparent",
        )
        self._brand_icon.pack(side="left", padx=(2, 10))
        self._brand_text = ctk.CTkFrame(self._brand, fg_color="transparent")
        self._brand_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            self._brand_text,
            text="SecureOffice",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            self._brand_text,
            text="Admin Console",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            anchor="w",
        ).pack(anchor="w")

        self._nav = ctk.CTkFrame(self, fg_color="transparent")
        self._nav.pack(fill="both", expand=True, padx=10)

        self._footer = ctk.CTkFrame(self, fg_color="transparent")
        self._footer.pack(fill="x", padx=10, pady=(0, 14))

        self._theme_button = ctk.CTkButton(
            self._footer,
            text="  Сменить тему",
            image=load_icon("sun" if theme.is_dark() else "moon", 18, "text_soft"),
            compound="left",
            anchor="w",
            fg_color="transparent",
            text_color=theme.palette_pair("text_soft"),
            hover_color=theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
            corner_radius=theme.RADIUS.md,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self._on_toggle_theme,
        )
        self._theme_button.pack(fill="x", pady=2)

        self._collapse_button = ctk.CTkButton(
            self._footer,
            text="  Свернуть",
            image=load_icon("chevron_left", 18, "text_soft"),
            compound="left",
            anchor="w",
            fg_color="transparent",
            text_color=theme.palette_pair("text_muted"),
            hover_color=theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
            corner_radius=theme.RADIUS.md,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.toggle,
        )
        self._collapse_button.pack(fill="x", pady=(8, 0))

    def add_item(self, item: NavItem) -> None:
        button = ctk.CTkButton(
            self._nav,
            text="  " + item.title,
            image=load_icon(item.icon, 20, "text_soft"),
            compound="left",
            anchor="w",
            fg_color="transparent",
            text_color=theme.palette_pair("text_soft"),
            hover_color=theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
            corner_radius=theme.RADIUS.md,
            height=42,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=lambda key=item.key: self._on_click(key),
        )
        button.pack(fill="x", pady=2)
        self._items[item.key] = {"button": button, "item": item}

    def _on_click(self, key: str) -> None:
        self.set_active(key)
        item = self._items[key]["item"]
        item.command()

    def set_active(self, key: str) -> None:
        self._active = key
        for k, payload in self._items.items():
            button = payload["button"]
            item = payload["item"]
            if k == key:
                button.configure(
                    fg_color=theme.palette_pair("primary_soft"),
                    text_color=theme.palette_pair("primary"),
                    image=load_icon(item.icon, 20, "primary"),
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=theme.palette_pair("text_soft"),
                    image=load_icon(item.icon, 20, "text_soft"),
                )

    def toggle(self) -> None:
        if self._expanded:
            self.configure(width=self.COLLAPSED_WIDTH)
            self._brand_text.pack_forget()
            for payload in self._items.values():
                item = payload["item"]
                payload["button"].configure(text="")
            self._theme_button.configure(text="")
            self._collapse_button.configure(text="")
        else:
            self.configure(width=self.EXPANDED_WIDTH)
            self._brand_text.pack(side="left", fill="x", expand=True)
            for payload in self._items.values():
                item = payload["item"]
                payload["button"].configure(text="  " + item.title)
            self._theme_button.configure(text="  Сменить тему")
            self._collapse_button.configure(text="  Свернуть")
        self._expanded = not self._expanded

    def update_theme_button(self) -> None:
        self._theme_button.configure(
            image=load_icon("sun" if theme.is_dark() else "moon", 18, "text_soft"),
        )

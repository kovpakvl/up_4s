"""Верхние вкладки с иконками — кастомный аналог CTkTabview.

В отличие от CTkTabview позволяет добавлять иконки и контролировать
анимацию подсветки активной вкладки.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon


@dataclass
class TabSpec:
    key: str
    title: str
    icon: str
    builder: Callable[[ctk.CTkFrame], None]


class TopTabs(ctk.CTkFrame):
    def __init__(self, master, *, on_change: Optional[Callable[[str], None]] = None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._tabs: dict[str, dict] = {}
        self._active: Optional[str] = None
        self._on_change = on_change

        self._strip = ctk.CTkFrame(
            self,
            corner_radius=theme.RADIUS.md,
            fg_color=theme.palette_pair("surface_soft"),
        )
        self._strip.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 16))

        self._strip_inner = ctk.CTkFrame(self._strip, fg_color="transparent")
        self._strip_inner.pack(side="left", padx=6, pady=6)

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.grid(row=1, column=0, sticky="nsew")
        self._body.grid_columnconfigure(0, weight=1)
        self._body.grid_rowconfigure(0, weight=1)

    def add_tab(self, spec: TabSpec) -> ctk.CTkFrame:
        button = ctk.CTkButton(
            self._strip_inner,
            text="  " + spec.title,
            image=load_icon(spec.icon, 18, "text_muted"),
            compound="left",
            anchor="center",
            fg_color="transparent",
            text_color=theme.palette_pair("text_muted"),
            hover_color=theme.color_pair(theme.LIGHT.surface, theme.DARK.surface_hi),
            corner_radius=theme.RADIUS.sm,
            height=38,
            width=138,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=lambda k=spec.key: self.activate(k),
        )
        button.pack(side="left", padx=2)
        frame = ctk.CTkFrame(self._body, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()
        # ленивая сборка содержимого
        self._tabs[spec.key] = {
            "spec": spec,
            "button": button,
            "frame": frame,
            "built": False,
        }
        return frame

    def activate(self, key: str) -> None:
        if key not in self._tabs:
            return
        for k, payload in self._tabs.items():
            button = payload["button"]
            frame = payload["frame"]
            spec = payload["spec"]
            if k == key:
                button.configure(
                    fg_color=theme.palette_pair("primary_soft"),
                    text_color=theme.palette_pair("primary"),
                    image=load_icon(spec.icon, 18, "primary"),
                )
                if not payload["built"]:
                    spec.builder(frame)
                    payload["built"] = True
                frame.grid()
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=theme.palette_pair("text_muted"),
                    image=load_icon(spec.icon, 18, "text_muted"),
                )
                frame.grid_remove()
        self._active = key
        if self._on_change:
            self._on_change(key)

    @property
    def active(self) -> Optional[str]:
        return self._active

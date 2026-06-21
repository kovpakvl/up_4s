"""Боковая выезжающая панель (drawer).

Реализована через `place` поверх контента. Анимация выезда — через `after`-tween.
"""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon


class Drawer(ctk.CTkFrame):
    def __init__(self, master, *, width: int = 380, **kwargs):
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("fg_color", theme.palette_pair("surface"))
        kwargs.setdefault("border_color", theme.palette_pair("line"))
        kwargs.setdefault("border_width", 1)
        super().__init__(master, width=width, **kwargs)
        self._master = master
        self._width = width
        self._open = False
        self._scrim: Optional[ctk.CTkFrame] = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=theme.SPACING.lg, pady=(theme.SPACING.lg, theme.SPACING.sm))
        self.title_label = ctk.CTkLabel(
            header,
            text="",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            anchor="w",
        )
        self.title_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            header,
            text="",
            image=load_icon("close", 16, "text_muted"),
            width=32,
            height=32,
            corner_radius=theme.RADIUS.sm,
            fg_color="transparent",
            hover_color=theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
            command=self.close,
        ).pack(side="right")

        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        self.body.pack(fill="both", expand=True, padx=theme.SPACING.lg, pady=(0, theme.SPACING.lg))

    def open(self, title: str = "") -> None:
        self.title_label.configure(text=title)
        for child in self.body.winfo_children():
            child.destroy()
        if self._open:
            return
        self._open = True
        self._scrim = ctk.CTkFrame(
            self._master,
            fg_color=theme.color_pair("#0B0D12", "#000000"),
            corner_radius=0,
        )
        self._scrim.place(relx=0, rely=0, relwidth=1, relheight=1)
        try:
            self._scrim._fg_color  # noqa: SLF001 — поддержим прозрачность через attributes
        except Exception:
            pass
        self._scrim.bind("<Button-1>", lambda _e: self.close())
        self._scrim.lift()

        self._master.update_idletasks()
        self.place(relx=1.0, rely=0, relheight=1.0, x=self._width, anchor="ne")
        self.lift()
        self._animate(start_offset=self._width, end_offset=0)

    def close(self) -> None:
        if not self._open:
            return
        self._open = False
        self._animate(start_offset=0, end_offset=self._width, on_end=self._after_close)

    def _after_close(self) -> None:
        self.place_forget()
        if self._scrim is not None:
            self._scrim.destroy()
            self._scrim = None

    def _animate(self, *, start_offset: int, end_offset: int, on_end=None, steps: int = 10) -> None:
        delta = (end_offset - start_offset) / steps

        def step(i: int) -> None:
            offset = int(start_offset + delta * i)
            try:
                self.place_configure(x=offset)
            except Exception:
                return
            if i < steps:
                self.after(14, lambda: step(i + 1))
            elif on_end:
                on_end()

        step(1)

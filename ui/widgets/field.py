"""Полевые виджеты с лейблом сверху, hint снизу и состоянием ошибки."""
from __future__ import annotations

from typing import Iterable, Optional

import customtkinter as ctk

from .. import theme


class _BaseField(ctk.CTkFrame):
    def __init__(self, master, label: str = "", hint: str = "", **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._label = None
        if label:
            self._label = ctk.CTkLabel(
                self,
                text=label,
                text_color=theme.palette_pair("text_soft"),
                fg_color="transparent",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                anchor="w",
            )
            self._label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self._hint = None
        if hint:
            self._hint_text = hint
            self._hint = ctk.CTkLabel(
                self,
                text=hint,
                text_color=theme.palette_pair("text_muted"),
                fg_color="transparent",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                anchor="w",
                justify="left",
            )
            self._hint.grid(row=2, column=0, sticky="w", pady=(6, 0))

    def set_error(self, message: Optional[str]) -> None:
        if self._hint is None:
            return
        if message:
            self._hint.configure(text=message, text_color=theme.palette_pair("danger"))
        else:
            self._hint.configure(
                text=getattr(self, "_hint_text", ""),
                text_color=theme.palette_pair("text_muted"),
            )


class LabeledEntry(_BaseField):
    def __init__(
        self,
        master,
        label: str = "",
        *,
        hint: str = "",
        placeholder: str = "",
        secret: bool = False,
        textvariable: Optional[ctk.StringVar] = None,
        width: int = 0,
        **kwargs,
    ):
        super().__init__(master, label=label, hint=hint, **kwargs)
        entry_kwargs = {
            "fg_color": theme.color_pair(theme.LIGHT.surface, theme.DARK.surface_soft),
            "text_color": theme.palette_pair("text"),
            "border_color": theme.palette_pair("line"),
            "border_width": 1,
            "corner_radius": theme.RADIUS.md,
            "height": 40,
            "placeholder_text": placeholder,
            "placeholder_text_color": theme.palette_pair("text_muted"),
            "font": ctk.CTkFont(family="Segoe UI", size=13),
        }
        if textvariable is not None:
            entry_kwargs["textvariable"] = textvariable
        if secret:
            entry_kwargs["show"] = "•"
        if width:
            entry_kwargs["width"] = width
        self.entry = ctk.CTkEntry(self, **entry_kwargs)
        self.entry.grid(row=1, column=0, sticky="ew")
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_blur)

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def focus(self) -> None:
        self.entry.focus_set()

    def _on_focus(self, _event=None) -> None:
        self.entry.configure(border_color=theme.palette_pair("primary"))

    def _on_blur(self, _event=None) -> None:
        self.entry.configure(border_color=theme.palette_pair("line"))


class LabeledTextArea(_BaseField):
    def __init__(
        self,
        master,
        label: str = "",
        *,
        hint: str = "",
        height: int = 110,
        **kwargs,
    ):
        super().__init__(master, label=label, hint=hint, **kwargs)
        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            corner_radius=theme.RADIUS.md,
            fg_color=theme.color_pair(theme.LIGHT.surface, theme.DARK.surface_soft),
            text_color=theme.palette_pair("text"),
            border_color=theme.palette_pair("line"),
            border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.textbox.grid(row=1, column=0, sticky="ew")

    def get(self) -> str:
        return self.textbox.get("1.0", "end").strip()

    def set(self, value: str) -> None:
        self.textbox.delete("1.0", "end")
        if value:
            self.textbox.insert("1.0", value)


class LabeledOptionMenu(_BaseField):
    def __init__(
        self,
        master,
        label: str = "",
        *,
        hint: str = "",
        values: Iterable[str] = (),
        variable: Optional[ctk.StringVar] = None,
        command=None,
        **kwargs,
    ):
        super().__init__(master, label=label, hint=hint, **kwargs)
        values = list(values) or [""]
        self.menu = ctk.CTkOptionMenu(
            self,
            values=values,
            variable=variable,
            command=command,
            fg_color=theme.color_pair(theme.LIGHT.surface, theme.DARK.surface_soft),
            button_color=theme.color_pair(theme.LIGHT.surface_hi, theme.DARK.surface_hi),
            button_hover_color=theme.color_pair(theme.LIGHT.line, theme.DARK.line_strong),
            text_color=theme.palette_pair("text"),
            dropdown_fg_color=theme.palette_pair("surface"),
            dropdown_text_color=theme.palette_pair("text"),
            dropdown_hover_color=theme.color_pair(theme.LIGHT.surface_hi, theme.DARK.surface_hi),
            corner_radius=theme.RADIUS.md,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.menu.grid(row=1, column=0, sticky="ew")

    def configure_values(self, values: Iterable[str]) -> None:
        self.menu.configure(values=list(values) or [""])

    def get(self) -> str:
        return self.menu.get()

    def set(self, value: str) -> None:
        self.menu.set(value)

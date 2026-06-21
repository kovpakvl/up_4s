"""Кнопки разных видов."""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon


class _BaseButton(ctk.CTkButton):
    def __init__(
        self,
        master,
        text: str = "",
        *,
        command: Optional[Callable] = None,
        icon: Optional[str] = None,
        icon_size: int = 18,
        height: int = 40,
        **kwargs,
    ):
        kwargs.setdefault("corner_radius", theme.RADIUS.md)
        kwargs.setdefault("height", height)
        kwargs.setdefault("font", ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        kwargs.setdefault("anchor", "center")
        if icon:
            kwargs["image"] = load_icon(icon, icon_size, self._icon_tone())
            kwargs.setdefault("compound", "left")
            if text:
                text = "  " + text
        super().__init__(master, text=text, command=command, **kwargs)

    def _icon_tone(self) -> str:
        return "text"


class PrimaryButton(_BaseButton):
    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("fg_color", theme.palette_pair("primary"))
        kwargs.setdefault("hover_color", theme.palette_pair("primary_hover"))
        kwargs.setdefault("text_color", theme.palette_pair("on_primary"))
        kwargs.setdefault("border_width", 0)
        super().__init__(master, text=text, **kwargs)

    def _icon_tone(self) -> str:
        return "on_primary"


class SecondaryButton(_BaseButton):
    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault(
            "fg_color", theme.color_pair(theme.LIGHT.surface, theme.DARK.surface_hi)
        )
        kwargs.setdefault(
            "hover_color",
            theme.color_pair(theme.LIGHT.surface_hi, theme.DARK.surface_soft),
        )
        kwargs.setdefault("text_color", theme.palette_pair("text"))
        kwargs.setdefault("border_color", theme.palette_pair("line"))
        kwargs.setdefault("border_width", 1)
        super().__init__(master, text=text, **kwargs)


class GhostButton(_BaseButton):
    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault(
            "hover_color",
            theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
        )
        kwargs.setdefault("text_color", theme.palette_pair("text_soft"))
        kwargs.setdefault("border_width", 0)
        super().__init__(master, text=text, **kwargs)

    def _icon_tone(self) -> str:
        return "text_soft"


class DangerButton(_BaseButton):
    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("fg_color", theme.palette_pair("danger"))
        kwargs.setdefault(
            "hover_color",
            theme.color_pair("#B91C1C", "#EF4444"),
        )
        kwargs.setdefault("text_color", "#FFFFFF")
        kwargs.setdefault("border_width", 0)
        super().__init__(master, text=text, **kwargs)

    def _icon_tone(self) -> str:
        return "text_inverse"


class IconButton(ctk.CTkButton):
    """Маленькая квадратная кнопка только с иконкой."""

    def __init__(
        self,
        master,
        icon: str,
        *,
        command: Optional[Callable] = None,
        size: int = 36,
        icon_size: int = 18,
        tone: str = "text_soft",
        tooltip: Optional[str] = None,
        **kwargs,
    ):
        self._command = command
        kwargs.setdefault("text", "")
        kwargs.setdefault("width", size)
        kwargs.setdefault("height", size)
        kwargs.setdefault("corner_radius", theme.RADIUS.md)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault(
            "hover_color",
            theme.color_pair(theme.LIGHT.surface_soft, theme.DARK.surface_soft),
        )
        kwargs.setdefault("border_width", 0)
        kwargs["image"] = load_icon(icon, icon_size, tone)
        super().__init__(master, command=self._invoke, **kwargs)
        self._tooltip = tooltip
        self._tip_label: Optional[ctk.CTkLabel] = None
        if tooltip:
            self.bind("<Enter>", self._show_tip)
            self.bind("<Leave>", self._hide_tip)
        self.bind("<ButtonPress>", self._hide_tip, add="+")
        self.bind("<Destroy>", self._hide_tip, add="+")
        self.bind("<Unmap>", self._hide_tip, add="+")
        self.bind("<FocusOut>", self._hide_tip, add="+")

    def _invoke(self) -> None:
        self._hide_tip()
        if self._command:
            self._command()

    def _show_tip(self, _event=None) -> None:
        if self._tip_label or not self._tooltip:
            return
        root = self.winfo_toplevel()
        label = ctk.CTkLabel(
            root,
            text=self._tooltip,
            text_color="#FFFFFF",
            fg_color=theme.palette_pair("overlay"),
            corner_radius=theme.RADIUS.sm,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            padx=10,
            pady=6,
        )
        label.update_idletasks()
        x = self.winfo_rootx() - root.winfo_rootx() + self.winfo_width() // 2
        y = self.winfo_rooty() - root.winfo_rooty() + self.winfo_height() + 6
        label.place(x=x, y=y, anchor="n")
        self._tip_label = label
        self.after(2200, self._hide_tip)

    def _hide_tip(self, _event=None) -> None:
        if self._tip_label:
            try:
                self._tip_label.destroy()
            except Exception:
                pass
            self._tip_label = None

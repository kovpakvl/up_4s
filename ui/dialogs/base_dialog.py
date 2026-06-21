"""Базовый модальный диалог поверх главного окна."""
from __future__ import annotations

import customtkinter as ctk

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.button import IconButton


class Dialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        title: str = "",
        *,
        width: int = 520,
        height: int = 420,
        resizable: bool = False,
    ):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=theme.palette_pair("bg"))
        if not resizable:
            self.resizable(False, False)
        self.transient(master)
        self.lift()
        self.attributes("-topmost", True)
        self.after(50, lambda: self.attributes("-topmost", False))

        self.update_idletasks()
        root_x = master.winfo_rootx()
        root_y = master.winfo_rooty()
        root_w = master.winfo_width()
        root_h = master.winfo_height()
        x = root_x + max((root_w - width) // 2, 0)
        y = root_y + max((root_h - height) // 2, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self._frame = ctk.CTkFrame(
            self,
            corner_radius=theme.RADIUS.lg,
            fg_color=theme.palette_pair("surface"),
            border_color=theme.palette_pair("line"),
            border_width=1,
        )
        self._frame.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkFrame(self._frame, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(20, 0))
        self.title_label = ctk.CTkLabel(
            header,
            text=title,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            anchor="w",
        )
        self.title_label.pack(side="left", fill="x", expand=True)
        IconButton(header, icon="close", command=self.destroy).pack(side="right")

        self.body = ctk.CTkFrame(self._frame, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=22, pady=(14, 16))

        self.footer = ctk.CTkFrame(self._frame, fg_color="transparent")
        self.footer.pack(fill="x", padx=22, pady=(0, 20))

        self._grab_done = False
        self.after(80, self._safe_grab)

    def _safe_grab(self) -> None:
        if self._grab_done:
            return
        try:
            self.grab_set()
            self._grab_done = True
        except Exception:
            pass

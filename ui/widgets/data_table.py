"""Современная "таблица" из карточек-строк.

В отличие от `ttk.Treeview` поддерживает произвольные ячейки (аватары,
бэйджи, inline-кнопки), hover-стейт всей строки и клики по конкретным
областям.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

import customtkinter as ctk

from .. import theme


@dataclass
class Column:
    key: str
    title: str
    weight: int = 1
    width: int = 0  # фиксированная ширина (если weight=0)
    align: str = "w"  # 'w' | 'center' | 'e'


CellBuilder = Callable[[ctk.CTkFrame, dict], None]
RowClick = Callable[[dict], None]


class DataTable(ctk.CTkFrame):
    def __init__(
        self,
        master,
        columns: Iterable[Column],
        *,
        cell_builders: Optional[dict[str, CellBuilder]] = None,
        on_row_click: Optional[RowClick] = None,
        row_padding: tuple[int, int] = (14, 14),
        **kwargs,
    ):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._columns = list(columns)
        self._cell_builders = cell_builders or {}
        self._on_row_click = on_row_click
        self._row_padding = row_padding

        # Заголовок
        self._header = ctk.CTkFrame(
            self,
            corner_radius=theme.RADIUS.md,
            fg_color=theme.palette_pair("surface_soft"),
        )
        self._header.pack(fill="x", padx=0, pady=(0, 8))
        self._configure_grid(self._header)
        for index, column in enumerate(self._columns):
            ctk.CTkLabel(
                self._header,
                text=column.title.upper(),
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                anchor=column.align,
                fg_color="transparent",
            ).grid(row=0, column=index, sticky="ew", padx=14, pady=10)

        self._list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
            scrollbar_button_hover_color=theme.palette_pair("text_muted"),
        )
        self._list.pack(fill="both", expand=True)
        self._list.grid_columnconfigure(0, weight=1)
        self._rows: list[ctk.CTkFrame] = []

    def _configure_grid(self, frame: ctk.CTkFrame) -> None:
        for index, column in enumerate(self._columns):
            frame.grid_columnconfigure(
                index,
                weight=column.weight,
                minsize=column.width or 0,
            )

    def clear(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()

    def set_rows(self, rows: Iterable[dict]) -> None:
        self.clear()
        for row_data in rows:
            self.add_row(row_data)

    def add_row(self, row_data: dict) -> None:
        row = ctk.CTkFrame(
            self._list,
            corner_radius=theme.RADIUS.md,
            fg_color=theme.palette_pair("surface"),
            border_color=theme.palette_pair("line"),
            border_width=1,
        )
        row.pack(fill="x", pady=4)
        self._configure_grid(row)
        for index, column in enumerate(self._columns):
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=14,
                pady=self._row_padding[0],
            )
            builder = self._cell_builders.get(column.key)
            if builder:
                builder(cell, row_data)
            else:
                value = row_data.get(column.key, "")
                ctk.CTkLabel(
                    cell,
                    text=str(value) if value not in (None, "") else "—",
                    text_color=theme.palette_pair("text"),
                    font=ctk.CTkFont(family="Segoe UI", size=13),
                    anchor=column.align,
                    fg_color="transparent",
                ).pack(fill="x", anchor=column.align)

        if self._on_row_click is not None:
            self._bind_click(row, row_data)

        self._rows.append(row)

    def _bind_click(self, row: ctk.CTkFrame, row_data: dict) -> None:
        def handler(_event=None) -> None:
            if self._on_row_click:
                self._on_row_click(row_data)

        def enter(_event=None) -> None:
            row.configure(fg_color=theme.palette_pair("surface_soft"))

        def leave(_event=None) -> None:
            row.configure(fg_color=theme.palette_pair("surface"))

        row.bind("<Enter>", enter)
        row.bind("<Leave>", leave)
        row.bind("<Button-1>", handler)
        for child in row.winfo_children():
            child.bind("<Enter>", enter)
            child.bind("<Leave>", leave)
            child.bind("<Button-1>", handler)
            for sub in child.winfo_children():
                if not isinstance(sub, ctk.CTkButton):
                    sub.bind("<Button-1>", handler)

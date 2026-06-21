"""Вкладка "Структура": отделы и должности компании."""
from __future__ import annotations

import threading

import customtkinter as ctk

from desktop.api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.badge import Badge
from ..widgets.button import GhostButton, IconButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card
from ..widgets.empty_state import EmptyState
from ..widgets.field import LabeledEntry


def build_structure_tab(parent: ctk.CTkFrame, app) -> None:
    tab = StructureTab(parent, app)
    tab.pack(fill="both", expand=True)


class StructureTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.departments: list[dict] = []

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # ─── список отделов ──────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        header = ctk.CTkFrame(left, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="Отделы",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="transparent",
        ).pack(side="left")
        SecondaryButton(
            header, text="Обновить", icon="refresh", height=34, command=self._reload
        ).pack(side="right")

        self.list_holder = ctk.CTkScrollableFrame(
            left, fg_color="transparent", scrollbar_button_color=theme.palette_pair("line_strong")
        )
        self.list_holder.pack(fill="both", expand=True, pady=(12, 0))
        self.list_holder.grid_columnconfigure(0, weight=1)

        # ─── правая колонка: формы добавления ────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        dep_card = Card(right)
        dep_card.pack(fill="x")
        ctk.CTkLabel(
            dep_card,
            text="Новый отдел",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
        ).pack(anchor="w", padx=20, pady=(18, 8))
        self.dep_name = LabeledEntry(dep_card, label="Название", placeholder="Например, IT")
        self.dep_name.pack(fill="x", padx=20)
        PrimaryButton(
            dep_card, text="Добавить отдел", icon="plus", command=self._add_department
        ).pack(fill="x", padx=20, pady=(14, 18))

        pos_card = Card(right)
        pos_card.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(
            pos_card,
            text="Новая должность",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
        ).pack(anchor="w", padx=20, pady=(18, 8))
        ctk.CTkLabel(
            pos_card,
            text="Выберите отдел в списке слева, затем введите название должности.",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            wraplength=260,
            justify="left",
            fg_color="transparent",
            anchor="w",
        ).pack(fill="x", padx=20)
        self.pos_dep_label = ctk.CTkLabel(
            pos_card,
            text="Отдел не выбран",
            text_color=theme.palette_pair("text_soft"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent",
            anchor="w",
        )
        self.pos_dep_label.pack(fill="x", padx=20, pady=(10, 2))
        self.pos_name = LabeledEntry(pos_card, label="Название должности", placeholder="Например, Менеджер")
        self.pos_name.pack(fill="x", padx=20)
        self.add_pos_btn = PrimaryButton(
            pos_card, text="Добавить должность", icon="plus", command=self._add_position
        )
        self.add_pos_btn.pack(fill="x", padx=20, pady=(14, 18))
        self._selected_dep_id: int | None = None

        self.after(80, self._reload)

    # ─── data ─────────────────────────────────────────────────────────
    def _reload(self) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.list_holder,
            text="Загружаю структуру…",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
        ).pack(pady=24)

        def worker() -> None:
            try:
                departments = self.app.state_obj.api.departments()
            except AdminApiError as exc:
                self.after(0, lambda error=str(exc): self._render_error(error))
                return
            self.after(0, lambda: self._render(departments))

        threading.Thread(target=worker, daemon=True).start()

    def _render_error(self, message: str) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        EmptyState(
            self.list_holder,
            icon="alert",
            title="Не удалось загрузить",
            description=message,
            action_text="Повторить",
            action_command=self._reload,
        ).pack(fill="both", expand=True)

    def _render(self, departments: list[dict]) -> None:
        self.departments = departments or []
        for child in self.list_holder.winfo_children():
            child.destroy()
        if not self.departments:
            EmptyState(
                self.list_holder,
                icon="building",
                title="Структура ещё пуста",
                description="Добавьте первый отдел справа, затем заведите должности.",
            ).pack(fill="both", expand=True)
            return
        for dep in self.departments:
            self._render_dep_card(dep)

    def _render_dep_card(self, dep: dict) -> None:
        card = Card(self.list_holder)
        card.pack(fill="x", pady=6)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=18)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")
        bubble = ctk.CTkFrame(
            header,
            width=36,
            height=36,
            corner_radius=12,
            fg_color=theme.palette_pair("primary_soft"),
        )
        bubble.pack(side="left")
        bubble.pack_propagate(False)
        ctk.CTkLabel(
            bubble,
            text="",
            image=load_icon("building", 20, "primary"),
            fg_color="transparent",
        ).pack(expand=True)
        name_block = ctk.CTkFrame(header, fg_color="transparent")
        name_block.pack(side="left", padx=(12, 0), fill="x", expand=True)
        ctk.CTkLabel(
            name_block,
            text=dep["name"],
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_block,
            text=f"должностей: {len(dep.get('positions', []))}",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            anchor="w",
        ).pack(anchor="w")
        SecondaryButton(
            header,
            text="Выбрать",
            icon="check",
            height=32,
            command=lambda d=dep: self._select_dep(d),
        ).pack(side="right")

        positions = dep.get("positions", [])
        chips_row = ctk.CTkFrame(inner, fg_color="transparent")
        chips_row.pack(fill="x", pady=(12, 0))
        if not positions:
            ctk.CTkLabel(
                chips_row,
                text="Должности ещё не заведены",
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="transparent",
            ).pack(anchor="w")
        else:
            wrap = ctk.CTkFrame(chips_row, fg_color="transparent")
            wrap.pack(anchor="w")
            for pos in positions:
                Badge(wrap, pos["name"], tone="neutral").pack(side="left", padx=(0, 6), pady=2)

    # ─── actions ──────────────────────────────────────────────────────
    def _select_dep(self, dep: dict) -> None:
        self._selected_dep_id = int(dep["id"])
        self.pos_dep_label.configure(
            text=f"Отдел: {dep['name']}",
            text_color=theme.palette_pair("primary"),
        )

    def _add_department(self) -> None:
        name = self.dep_name.get().strip()
        if not name:
            self.app.toasts.show("Введите название отдела", tone="warning")
            return
        try:
            self.app.state_obj.api.create_department(name)
        except AdminApiError as exc:
            self.app.toasts.show(str(exc), tone="danger")
            return
        self.app.toasts.show(f"Отдел «{name}» добавлен", tone="success")
        self.dep_name.set("")
        self.app.state_obj.mark_done("department")
        self._reload()

    def _add_position(self) -> None:
        if self._selected_dep_id is None:
            self.app.toasts.show("Сначала выберите отдел", tone="warning")
            return
        name = self.pos_name.get().strip()
        if not name:
            self.app.toasts.show("Введите название должности", tone="warning")
            return
        try:
            self.app.state_obj.api.create_position(self._selected_dep_id, name)
        except AdminApiError as exc:
            self.app.toasts.show(str(exc), tone="danger")
            return
        self.app.toasts.show(f"Должность «{name}» добавлена", tone="success")
        self.pos_name.set("")
        self._reload()

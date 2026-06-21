"""Вкладка "Сотрудники" — карточки людей, поиск, выдача доступа."""
from __future__ import annotations

import threading
from typing import Optional

import customtkinter as ctk

from desktop.api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.avatar import Avatar
from ..widgets.badge import Badge
from ..widgets.button import GhostButton, IconButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card
from ..widgets.empty_state import EmptyState
from ..widgets.field import LabeledEntry, LabeledOptionMenu
from ..dialogs.activation_key import show_activation_key
from ..dialogs.confirm import confirm
from ..dialogs.employee_form import open_employee_form


def build_employees_tab(parent: ctk.CTkFrame, app) -> None:
    tab = EmployeesTab(parent, app)
    tab.pack(fill="both", expand=True)


class EmployeesTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.employees: list[dict] = []
        self.departments: list[dict] = []
        self.filtered: list[dict] = []
        self.search_term = ""
        self.dep_filter = "Все отделы"

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 14))

        # actions всегда справа, поля растягиваются слева
        actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions.pack(side="right", padx=(12, 0), pady=(22, 0))
        PrimaryButton(
            actions,
            text="Добавить сотрудника",
            icon="plus",
            command=self._open_new_employee,
        ).pack(side="right")
        SecondaryButton(
            actions, text="Обновить", icon="refresh", command=self._reload
        ).pack(side="right", padx=(0, 8))

        fields = ctk.CTkFrame(toolbar, fg_color="transparent")
        fields.pack(side="left", fill="x", expand=True)
        fields.grid_columnconfigure(0, weight=2)
        fields.grid_columnconfigure(1, weight=1)

        self.search_field = LabeledEntry(
            fields, label="Поиск", placeholder="ФИО, email, телефон"
        )
        self.search_field.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.search_field.entry.bind("<KeyRelease>", self._on_search)

        self.dep_field = LabeledOptionMenu(
            fields, label="Отдел", values=["Все отделы"]
        )
        self.dep_field.menu.configure(command=self._on_dep_change)
        self.dep_field.grid(row=0, column=1, sticky="ew")

        self.list_holder = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        self.list_holder.pack(fill="both", expand=True)
        self.list_holder.grid_columnconfigure(0, weight=1)

        self.after(80, self._reload)

    # ─── data ─────────────────────────────────────────────────────────
    def _reload(self) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        self._render_loading()

        def worker() -> None:
            try:
                employees = self.app.state_obj.api.employees()
                departments = self.app.state_obj.api.departments()
            except AdminApiError as exc:
                self.after(0, lambda error=str(exc): self._render_error(error))
                return
            self.after(0, lambda: self._apply(employees, departments))

        threading.Thread(target=worker, daemon=True).start()

    def _apply(self, employees: list[dict], departments: list[dict]) -> None:
        self.employees = employees or []
        self.departments = departments or []
        labels = ["Все отделы"] + [d["name"] for d in self.departments]
        self.dep_field.configure_values(labels)
        if self.dep_filter not in labels:
            self.dep_filter = "Все отделы"
            self.dep_field.set("Все отделы")
        self._render_list()

    # ─── ui ───────────────────────────────────────────────────────────
    def _render_loading(self) -> None:
        ctk.CTkLabel(
            self.list_holder,
            text="Загружаю сотрудников…",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
        ).pack(pady=40)

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

    def _render_list(self) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        items = self._filter()
        if not items:
            if not self.employees:
                EmptyState(
                    self.list_holder,
                    icon="users",
                    title="Сотрудников пока нет",
                    description="Добавьте первого человека и выдайте ему ключ активации.",
                    action_text="Добавить сотрудника",
                    action_command=self._open_new_employee,
                ).pack(fill="both", expand=True)
            else:
                EmptyState(
                    self.list_holder,
                    icon="search",
                    title="Ничего не найдено",
                    description="Поменяйте запрос или сбросьте фильтр по отделу.",
                ).pack(fill="both", expand=True)
            return

        for employee in items:
            self._render_card(employee)

    def _filter(self) -> list[dict]:
        items = self.employees
        if self.search_term:
            term = self.search_term.lower()
            items = [
                e
                for e in items
                if term in (e.get("full_name", "") or "").lower()
                or term in (e.get("email", "") or "").lower()
                or term in (e.get("phone", "") or "").lower()
            ]
        if self.dep_filter and self.dep_filter != "Все отделы":
            items = [e for e in items if e.get("department_name") == self.dep_filter]
        return items

    def _render_card(self, employee: dict) -> None:
        card = Card(self.list_holder)
        card.pack(fill="x", pady=6)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=18)
        row.grid_columnconfigure(2, weight=1)

        Avatar(row, employee.get("full_name", ""), size=46).grid(row=0, column=0, rowspan=2, sticky="n")

        name_block = ctk.CTkFrame(row, fg_color="transparent")
        name_block.grid(row=0, column=1, columnspan=3, sticky="w", padx=(14, 0))
        ctk.CTkLabel(
            name_block,
            text=employee.get("full_name", "—"),
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="transparent",
        ).pack(side="left")
        if employee.get("has_user"):
            Badge(name_block, "Активен", tone="success").pack(side="left", padx=(10, 0))
        else:
            Badge(name_block, "Ожидает активации", tone="warning").pack(side="left", padx=(10, 0))

        meta_text = " · ".join(
            filter(
                None,
                [
                    employee.get("department_name") or "Без отдела",
                    employee.get("position_name") or "",
                ],
            )
        )
        ctk.CTkLabel(
            row,
            text=meta_text,
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=(14, 0), pady=(4, 0))

        contacts = " · ".join(
            filter(None, [employee.get("email") or "", employee.get("phone") or ""])
        )
        ctk.CTkLabel(
            row,
            text=contacts or "Контакты не указаны",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            anchor="w",
        ).grid(row=1, column=2, sticky="w", padx=(20, 0), pady=(4, 0))

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=3, rowspan=2, sticky="e")
        SecondaryButton(
            actions,
            text="Выдать ключ",
            icon="key",
            height=34,
            command=lambda e=employee: self._issue_key(e),
        ).pack(side="left", padx=(0, 6))
        IconButton(
            actions,
            icon="copy",
            tooltip="Скопировать email",
            command=lambda e=employee: self._copy_email(e),
        ).pack(side="left")

    # ─── actions ──────────────────────────────────────────────────────
    def _on_search(self, _event=None) -> None:
        self.search_term = self.search_field.get().strip()
        self._render_list()

    def _on_dep_change(self, value: str) -> None:
        self.dep_filter = value
        self._render_list()

    def _open_new_employee(self) -> None:
        def on_created(employee: dict, key_payload: dict) -> None:
            self._reload()
            self.app.state_obj.update_urls()
            show_activation_key(
                self.app,
                employee=employee,
                code=key_payload["code"],
                expires_at=key_payload.get("expires_at", ""),
                activation_url=self.app.state_obj.activation_url,
            )

        if not self.departments:
            # Подгрузим отделы перед открытием формы
            try:
                self.departments = self.app.state_obj.api.departments() or []
            except AdminApiError as exc:
                self.app.toasts.show(str(exc), tone="danger")
                return
        open_employee_form(self.app, self.departments, on_created)

    def _issue_key(self, employee: dict) -> None:
        def execute() -> None:
            try:
                payload = self.app.state_obj.api.create_activation_key(int(employee["id"]))
            except AdminApiError as exc:
                self.app.toasts.show(str(exc), tone="danger")
                return
            self.app.state_obj.update_urls()
            show_activation_key(
                self.app,
                employee=employee,
                code=payload["code"],
                expires_at=payload.get("expires_at", ""),
                activation_url=self.app.state_obj.activation_url,
            )
            self._reload()

        if employee.get("has_user"):
            confirm(
                self.app,
                title="Перевыпустить ключ?",
                message=(
                    f"{employee.get('full_name', '')} уже активировал доступ. "
                    "Новый ключ перезапишет старый, текущая учётная запись останется работать."
                ),
                confirm_text="Перевыпустить",
                tone="warning",
                icon="key",
                on_confirm=execute,
            )
        else:
            execute()

    def _copy_email(self, employee: dict) -> None:
        email = employee.get("email") or ""
        if not email:
            self.app.toasts.show("У сотрудника нет email", tone="warning")
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(email)
        self.app.toasts.show("Email скопирован", tone="success")

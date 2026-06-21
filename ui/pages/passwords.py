"""Вкладка "Пароли" — корпоративные учётные записи."""
from __future__ import annotations

import threading
from urllib.parse import urlparse

import customtkinter as ctk

from desktop.api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.badge import Badge
from ..widgets.button import GhostButton, IconButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card
from ..widgets.empty_state import EmptyState
from ..widgets.field import LabeledEntry
from ..dialogs.confirm import confirm
from ..dialogs.password_form import open_password_form


def build_passwords_tab(parent: ctk.CTkFrame, app) -> None:
    tab = PasswordsTab(parent, app)
    tab.pack(fill="both", expand=True)


class PasswordsTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.entries: list[dict] = []
        self.employees: list[dict] = []
        self.search_term = ""

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 14))

        actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions.pack(side="right", padx=(12, 0), pady=(22, 0))
        PrimaryButton(
            actions,
            text="Добавить",
            icon="plus",
            width=146,
            command=self._open_new_entry,
        ).pack(side="right")
        SecondaryButton(
            actions,
            text="Обновить",
            icon="refresh",
            width=140,
            command=self._reload,
        ).pack(side="right", padx=(0, 8))

        fields = ctk.CTkFrame(toolbar, fg_color="transparent")
        fields.pack(side="left", fill="x", expand=True)

        self.search_field = LabeledEntry(
            fields,
            label="Поиск",
            placeholder="Сервис, логин, сотрудник",
        )
        self.search_field.pack(fill="x")
        self.search_field.entry.bind("<KeyRelease>", self._on_search)

        self.list_holder = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        self.list_holder.pack(fill="both", expand=True)
        self.list_holder.grid_columnconfigure(0, weight=1)

        self._revealed: set[int] = set()

        self.after(80, self._reload)

    # ─── data ─────────────────────────────────────────────────────────
    def _reload(self) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.list_holder,
            text="Загружаю записи…",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
        ).pack(pady=40)

        def worker() -> None:
            try:
                entries = self.app.state_obj.api.password_entries()
                employees = self.app.state_obj.api.employees()
            except AdminApiError as exc:
                self.after(0, lambda error=str(exc): self._render_error(error))
                return
            self.after(0, lambda: self._apply(entries, employees))

        threading.Thread(target=worker, daemon=True).start()

    def _apply(self, entries: list[dict], employees: list[dict]) -> None:
        self.entries = entries or []
        self.employees = employees or []
        self._render()

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

    def _render(self) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        items = self._filter()
        if not items:
            if not self.entries:
                EmptyState(
                    self.list_holder,
                    icon="key",
                    title="Записей паролей пока нет",
                    description="Создайте первую запись и привяжите её к сотрудникам.",
                    action_text="Добавить запись",
                    action_command=self._open_new_entry,
                ).pack(fill="both", expand=True)
            else:
                EmptyState(
                    self.list_holder,
                    icon="search",
                    title="Ничего не найдено",
                    description="Попробуйте сменить поисковый запрос.",
                ).pack(fill="both", expand=True)
            return
        for entry in items:
            self._render_entry(entry)

    def _filter(self) -> list[dict]:
        if not self.search_term:
            return self.entries
        term = self.search_term.lower()
        return [
            e
            for e in self.entries
            if term in (e.get("service_name", "") or "").lower()
            or term in (e.get("login", "") or "").lower()
            or term in (e.get("employee_name", "") or "").lower()
        ]

    def _render_entry(self, entry: dict) -> None:
        card = Card(self.list_holder)
        card.pack(fill="x", pady=6)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=18)
        body.grid_columnconfigure(1, weight=1, minsize=220)
        body.grid_columnconfigure(2, weight=0, minsize=260)

        bubble = ctk.CTkFrame(
            body,
            width=44,
            height=44,
            corner_radius=14,
            fg_color=theme.palette_pair("primary_soft"),
        )
        bubble.grid(row=0, column=0, rowspan=2, sticky="n")
        bubble.grid_propagate(False)
        initials = _service_initials(entry.get("service_name", ""))
        ctk.CTkLabel(
            bubble,
            text=initials,
            text_color=theme.palette_pair("primary"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
        ).pack(expand=True, pady=(2, 0))

        name_block = ctk.CTkFrame(body, fg_color="transparent")
        name_block.grid(row=0, column=1, sticky="ew", padx=(14, 16))
        name_block.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            name_block,
            text=("★ " if entry.get("is_favorite") else "") + entry.get("service_name", "—"),
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="transparent",
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        login = entry.get("login") or "—"
        ctk.CTkLabel(
            body,
            text=f"{entry.get('employee_name', '—')}  ·  {login}",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=(14, 0), pady=(4, 0))

        password_block = ctk.CTkFrame(body, fg_color="transparent")
        password_block.grid(row=0, column=2, sticky="e", pady=(0, 0))

        revealed = int(entry["id"]) in self._revealed
        pwd_label = ctk.CTkLabel(
            password_block,
            text=entry.get("password", "") if revealed else "••••••••••••",
            width=150,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="transparent",
            anchor="e",
        )
        pwd_label.pack(side="left", padx=(0, 6))
        IconButton(
            password_block,
            icon="eye",
            tooltip="Показать на 8 сек." if not revealed else "Скрыть",
            command=lambda e=entry, lbl=pwd_label: self._toggle_password(e, lbl),
        ).pack(side="left")
        IconButton(
            password_block,
            icon="copy",
            tooltip="Скопировать пароль",
            command=lambda e=entry: self._copy_password(e),
        ).pack(side="left", padx=(4, 0))

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(row=1, column=2, sticky="e", pady=(8, 0))
        GhostButton(
            actions,
            text="История",
            icon="activity",
            height=30,
            command=lambda e=entry: self._open_history(e),
        ).pack(side="left", padx=(0, 6))
        GhostButton(
            actions,
            text="Изменить",
            icon="gear",
            height=30,
            command=lambda e=entry: self._open_edit(e),
        ).pack(side="left", padx=(0, 6))
        IconButton(
            actions,
            icon="trash",
            tooltip="Удалить",
            command=lambda e=entry: self._delete(e),
        ).pack(side="left")

    # ─── actions ──────────────────────────────────────────────────────
    def _on_search(self, _event=None) -> None:
        self.search_term = self.search_field.get().strip()
        self._render()

    def _toggle_password(self, entry: dict, label: ctk.CTkLabel) -> None:
        eid = int(entry["id"])
        if eid in self._revealed:
            self._revealed.discard(eid)
            label.configure(text="••••••••••••")
            return
        self._revealed.add(eid)
        label.configure(text=entry.get("password", ""))
        self.after(8000, lambda: self._auto_hide(eid, label))

    def _auto_hide(self, eid: int, label: ctk.CTkLabel) -> None:
        if eid in self._revealed:
            self._revealed.discard(eid)
            try:
                label.configure(text="••••••••••••")
            except Exception:
                pass

    def _copy_password(self, entry: dict) -> None:
        value = entry.get("password", "")
        if not value:
            self.app.toasts.show("Пароль пуст", tone="warning")
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(value)
        self.app.toasts.show("Пароль скопирован", tone="success")

    def _open_new_entry(self) -> None:
        if not self.employees:
            try:
                self.employees = self.app.state_obj.api.employees() or []
            except AdminApiError as exc:
                self.app.toasts.show(str(exc), tone="danger")
                return
        if not self.employees:
            self.app.toasts.show("Сначала добавьте хотя бы одного сотрудника", tone="warning")
            return
        open_password_form(
            self.app,
            employees=self.employees,
            on_done=self._reload,
        )

    def _open_edit(self, entry: dict) -> None:
        if not self.employees:
            try:
                self.employees = self.app.state_obj.api.employees() or []
            except AdminApiError:
                pass
        open_password_form(
            self.app,
            employees=self.employees,
            entry=entry,
            on_done=self._reload,
        )

    def _open_history(self, entry: dict) -> None:
        try:
            history = self.app.state_obj.api.password_history(int(entry["id"]))
        except AdminApiError as exc:
            self.app.toasts.show(str(exc), tone="danger")
            return
        from ..dialogs.history import show_password_history
        show_password_history(self.app, entry=entry, history=history)

    def _delete(self, entry: dict) -> None:
        confirm(
            self.app,
            title="Удалить запись?",
            message=f"Запись «{entry.get('service_name', '')}» будет безвозвратно удалена.",
            confirm_text="Удалить",
            tone="danger",
            icon="trash",
            on_confirm=lambda: self._do_delete(entry),
        )

    def _do_delete(self, entry: dict) -> None:
        try:
            self.app.state_obj.api.delete_password_entry(int(entry["id"]))
        except AdminApiError as exc:
            self.app.toasts.show(str(exc), tone="danger")
            return
        self.app.toasts.show("Запись удалена", tone="success")
        self._reload()


def _service_initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[1][:1]).upper()

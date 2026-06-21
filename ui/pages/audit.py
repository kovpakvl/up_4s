"""Страница "Журнал" — таймлайн событий с фильтрами."""
from __future__ import annotations

import threading

import customtkinter as ctk

from desktop.api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..time_utils import format_moscow_datetime, format_moscow_day, format_moscow_time
from ..widgets.badge import Badge
from ..widgets.button import SecondaryButton
from ..widgets.card import Card
from ..widgets.empty_state import EmptyState
from ..widgets.field import LabeledEntry, LabeledOptionMenu
from .base import Page


_EVENT_META = {
    "admin.created": ("Создан администратор", "success", "user"),
    "auth.login": ("Вход в систему", "info", "lock"),
    "auth.login_failed": ("Неудачная попытка входа", "danger", "alert"),
    "department.created": ("Добавлен отдел", "primary", "building"),
    "position.created": ("Добавлена должность", "primary", "building"),
    "employee.created": ("Добавлен сотрудник", "primary", "users"),
    "activation_key.created": ("Выдан ключ сотруднику", "info", "key"),
    "employee.activated": ("Сотрудник активировал доступ", "success", "check"),
    "password_entry.created": ("Добавлена запись пароля", "success", "key"),
    "password_entry.updated": ("Изменена запись пароля", "warning", "refresh"),
    "password_entry.deleted": ("Удалена запись пароля", "danger", "trash"),
}


class AuditPage(Page):
    title = "Журнал"
    subtitle = "Хронология действий и попыток входа"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.events: list[dict] = []
        self.event_filter = "Все события"

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=(20, 14))
        toolbar.grid_columnconfigure(0, weight=1)
        toolbar.grid_columnconfigure(1, weight=1)

        self.search_field = LabeledEntry(toolbar, label="Поиск", placeholder="Кто, что, какой объект")
        self.search_field.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.search_field.entry.bind("<KeyRelease>", lambda _e: self._render())

        self.filter_field = LabeledOptionMenu(
            toolbar,
            label="Тип события",
            values=["Все события"] + sorted({label for label, *_ in _EVENT_META.values()}),
        )
        self.filter_field.menu.configure(command=self._on_filter_change)
        self.filter_field.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        SecondaryButton(
            toolbar, text="Обновить", icon="refresh", command=self._reload
        ).grid(row=0, column=2, sticky="e", pady=(22, 0))

        self.timeline = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        self.timeline.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.timeline.grid_columnconfigure(0, weight=1)

        self.after(80, self._reload)

    def on_enter(self) -> None:
        # обновляем при заходе в раздел
        self._reload()

    def _on_filter_change(self, value: str) -> None:
        self.event_filter = value
        self._render()

    def _reload(self) -> None:
        for child in self.timeline.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.timeline,
            text="Загружаю события…",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
        ).pack(pady=40)

        def worker() -> None:
            try:
                events = self.app.state_obj.api.audit_events(limit=300)
            except AdminApiError as exc:
                self.after(0, lambda error=str(exc): self._render_error(error))
                return
            self.after(0, lambda: self._apply(events))

        threading.Thread(target=worker, daemon=True).start()

    def _apply(self, events: list[dict]) -> None:
        self.events = events or []
        self._render()

    def _render_error(self, message: str) -> None:
        for child in self.timeline.winfo_children():
            child.destroy()
        EmptyState(
            self.timeline,
            icon="alert",
            title="Не удалось загрузить",
            description=message,
            action_text="Повторить",
            action_command=self._reload,
        ).pack(fill="both", expand=True)

    def _render(self) -> None:
        for child in self.timeline.winfo_children():
            child.destroy()
        items = self._filter()
        if not items:
            EmptyState(
                self.timeline,
                icon="activity",
                title="Событий не найдено",
                description="Попробуйте сменить фильтр или поиск.",
            ).pack(fill="both", expand=True)
            return

        previous_day = None
        for event in items:
            day = _format_day(event.get("created_at", ""))
            if day != previous_day and day:
                ctk.CTkLabel(
                    self.timeline,
                    text=day,
                    text_color=theme.palette_pair("text_muted"),
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    fg_color="transparent",
                    anchor="w",
                ).pack(fill="x", padx=4, pady=(14, 6))
                previous_day = day
            self._render_event(event)

    def _filter(self) -> list[dict]:
        items = self.events
        term = self.search_field.get().strip().lower()
        if term:
            items = [
                e
                for e in items
                if term in (e.get("actor_name") or "").lower()
                or term in (e.get("actor_username") or "").lower()
                or term in (e.get("event_type", "") or "").lower()
                or term in str(e.get("details", "")).lower()
            ]
        if self.event_filter and self.event_filter != "Все события":
            items = [
                e
                for e in items
                if _EVENT_META.get(e.get("event_type", ""), ("", "", ""))[0] == self.event_filter
            ]
        return items

    def _render_event(self, event: dict) -> None:
        label, tone, icon_name = _EVENT_META.get(
            event.get("event_type", ""),
            (event.get("event_type", "Событие"), "info", "activity"),
        )
        card = Card(self.timeline)
        card.pack(fill="x", pady=4)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=14)
        row.grid_columnconfigure(1, weight=1)

        bubble = ctk.CTkFrame(
            row,
            width=42,
            height=42,
            corner_radius=14,
            fg_color=theme.palette_pair(f"{tone}_soft"),
        )
        bubble.grid(row=0, column=0, rowspan=2, sticky="n")
        bubble.grid_propagate(False)
        ctk.CTkLabel(
            bubble,
            text="",
            image=load_icon(icon_name, 20, tone),
            fg_color="transparent",
        ).pack(expand=True)

        head = ctk.CTkFrame(row, fg_color="transparent")
        head.grid(row=0, column=1, sticky="w", padx=(14, 0))
        ctk.CTkLabel(
            head,
            text=label,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="transparent",
        ).pack(side="left")
        actor = event.get("actor_name") or event.get("actor_username") or "Система"
        ctk.CTkLabel(
            row,
            text=f"{actor} · {_format_time(event.get('created_at', ''))}",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=(14, 0), pady=(2, 0))

        details = _format_details(event.get("details") or {})
        if details:
            ctk.CTkLabel(
                row,
                text=details,
                text_color=theme.palette_pair("text_soft"),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color="transparent",
                wraplength=520,
                justify="left",
                anchor="w",
            ).grid(row=2, column=1, sticky="w", padx=(14, 0), pady=(6, 0))


def _format_day(value: str) -> str:
    return format_moscow_day(value)


def _format_time(value: str) -> str:
    return format_moscow_time(value)


def _format_details(details: dict) -> str:
    if not details:
        return ""
    parts: list[str] = []
    if "name" in details:
        parts.append(f"Название: {details['name']}")
    if "expires_at" in details:
        parts.append(f"Действует до: {format_moscow_datetime(details['expires_at'])}")
    if "password_changed" in details:
        parts.append("Пароль изменён" if details["password_changed"] else "Пароль не менялся")
    return " · ".join(parts)

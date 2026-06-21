"""Содержимое вкладки "Обзор" — сводка для администратора."""
from __future__ import annotations

import threading
from typing import Iterable, Optional

import customtkinter as ctk

from admin_api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..time_utils import seconds_since, to_moscow
from ..widgets.badge import Badge
from ..widgets.button import GhostButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card
from ..widgets.stat_card import StatCard


_EVENT_LABELS = {
    "admin.created": ("Создан администратор", "success"),
    "auth.login": ("Вход в систему", "info"),
    "auth.login_failed": ("Неудачная попытка входа", "danger"),
    "department.created": ("Добавлен отдел", "primary"),
    "position.created": ("Добавлена должность", "primary"),
    "employee.created": ("Добавлен сотрудник", "primary"),
    "activation_key.created": ("Выдан ключ сотруднику", "info"),
    "employee.activated": ("Сотрудник активировал доступ", "success"),
    "password_entry.created": ("Добавлена запись пароля", "success"),
    "password_entry.updated": ("Изменена запись пароля", "warning"),
    "password_entry.deleted": ("Удалена запись пароля", "danger"),
}


def _format_time(value: str) -> str:
    seconds = seconds_since(value)
    if seconds is None:
        return str(value or "")
    if seconds < 60:
        return "только что"
    if seconds < 3600:
        return f"{seconds // 60} мин назад"
    if seconds < 86400:
        return f"{seconds // 3600} ч назад"
    if seconds < 604800:
        return f"{seconds // 86400} дн назад"
    dt = to_moscow(value)
    return f"{dt:%d.%m.%Y %H:%M} МСК" if dt else str(value or "")


class OverviewTab(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(
            master,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        self.app = app

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        # ─── левая колонка ───────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.grid_columnconfigure(0, weight=1)

        # 1. hero "что требует внимания"
        self.hero = Card(left)
        self.hero.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self._build_hero(self.hero)

        # 2. карточки статистики
        stats = ctk.CTkFrame(left, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)

        self.card_employees = StatCard(stats, icon="users", label="Сотрудники", tone="primary")
        self.card_employees.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.card_passwords = StatCard(stats, icon="key", label="Записей паролей", tone="info")
        self.card_passwords.grid(row=0, column=1, sticky="nsew", padx=8)
        self.card_pending = StatCard(stats, icon="mail", label="Ждут активации", tone="warning")
        self.card_pending.grid(row=0, column=2, sticky="nsew", padx=8)
        self.card_events = StatCard(stats, icon="activity", label="События за сутки", tone="success")
        self.card_events.grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        # 3. чек-лист первого дня
        self.checklist_card = Card(left)
        self.checklist_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self._build_checklist_skeleton()

        # ─── правая колонка ──────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.events_card = Card(right)
        self.events_card.grid(row=0, column=0, sticky="nsew")
        self._build_events_skeleton()

        self.after(80, self.refresh)

    # ─── скелеты ─────────────────────────────────────────────────────
    def _build_hero(self, parent: ctk.CTkFrame) -> None:
        for child in parent.winfo_children():
            child.destroy()
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=22)
        inner.grid_columnconfigure(1, weight=1)

        bubble = ctk.CTkFrame(
            inner,
            width=58,
            height=58,
            corner_radius=18,
            fg_color=theme.palette_pair("primary_soft"),
        )
        bubble.grid(row=0, column=0, rowspan=2, sticky="n")
        bubble.grid_propagate(False)
        ctk.CTkLabel(
            bubble,
            text="",
            image=load_icon("shield", 28, "primary"),
            fg_color="transparent",
        ).pack(expand=True)

        self.hero_title = ctk.CTkLabel(
            inner,
            text="Загружаю данные…",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            fg_color="transparent",
            anchor="w",
        )
        self.hero_title.grid(row=0, column=1, sticky="w", padx=(16, 0))
        self.hero_subtitle = ctk.CTkLabel(
            inner,
            text=" ",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            anchor="w",
            wraplength=560,
            justify="left",
        )
        self.hero_subtitle.grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(2, 12))

        self.hero_alerts = ctk.CTkFrame(inner, fg_color="transparent")
        self.hero_alerts.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=2, sticky="w", pady=(16, 0))
        PrimaryButton(
            actions,
            text="Добавить сотрудника",
            icon="plus",
            command=lambda: self._switch_tab("employees"),
        ).pack(side="left")
        SecondaryButton(
            actions,
            text="Добавить пароль",
            icon="key",
            command=lambda: self._switch_tab("passwords"),
        ).pack(side="left", padx=(8, 0))
        GhostButton(
            actions,
            text="Открыть обучение",
            icon="help",
            command=self._open_tutorial,
        ).pack(side="left", padx=(8, 0))

    def _build_checklist_skeleton(self) -> None:
        for child in self.checklist_card.winfo_children():
            child.destroy()
        inner = ctk.CTkFrame(self.checklist_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=22)
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="Чек-лист первого дня",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="transparent",
        ).pack(side="left")
        self.checklist_progress = Badge(header, "0 из 4", tone="primary")
        self.checklist_progress.pack(side="right")
        self.checklist_body = ctk.CTkFrame(inner, fg_color="transparent")
        self.checklist_body.pack(fill="x", pady=(14, 0))

    def _build_events_skeleton(self) -> None:
        for child in self.events_card.winfo_children():
            child.destroy()
        inner = ctk.CTkFrame(self.events_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=22)
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="Лента событий",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="transparent",
        ).pack(side="left")
        GhostButton(
            header,
            text="Журнал",
            icon="arrow_right",
            command=lambda: self.app.show_page("audit"),
        ).pack(side="right")
        self.events_body = ctk.CTkFrame(inner, fg_color="transparent")
        self.events_body.pack(fill="both", expand=True, pady=(14, 0))

    # ─── данные ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._set_hero_loading()

        def worker() -> None:
            data: dict = {}
            if not self.app.state_obj.api.token:
                self.after(0, lambda: self._apply(None))
                return
            try:
                data["employees"] = self.app.state_obj.api.employees()
                data["passwords"] = self.app.state_obj.api.password_entries()
                data["audit"] = self.app.state_obj.api.audit_events(limit=80)
            except AdminApiError as exc:
                self.after(0, lambda error=str(exc): self._apply(None, error=error))
                return
            self.after(0, lambda payload=data: self._apply(payload))

        threading.Thread(target=worker, daemon=True).start()

    def _apply(self, data: Optional[dict], error: Optional[str] = None) -> None:
        if data is None:
            self.hero_title.configure(text="Нет соединения с сервером")
            self.hero_subtitle.configure(
                text=error or "Войдите заново или запустите сервер, чтобы увидеть метрики."
            )
            self._render_alerts([])
            return
        employees = data.get("employees", [])
        passwords = data.get("passwords", [])
        audit = data.get("audit", [])

        pending = sum(1 for e in employees if not e.get("has_user"))
        weak = sum(1 for p in passwords if _is_weak(p.get("password", "")))
        stale = sum(1 for p in passwords if _is_stale(p.get("password_changed_at")))
        events_today = sum(1 for e in audit if _is_today(e.get("created_at", "")))

        self.card_employees.set_value(str(len(employees)), hint="всего в системе")
        self.card_passwords.set_value(str(len(passwords)), hint="учётных записей")
        self.card_pending.set_value(str(pending), hint="ключ не активирован")
        self.card_events.set_value(str(events_today), hint="за последние 24 ч")

        alerts: list[tuple[str, str, str]] = []
        if pending:
            alerts.append(
                (
                    f"{pending} сотрудник{'ов' if pending != 1 else ''} ещё не активировал доступ",
                    "warning",
                    "users",
                )
            )
        if weak:
            alerts.append(
                (f"{weak} слабых пароля требуют усиления", "danger", "alert")
            )
        if stale:
            alerts.append(
                (f"{stale} пароля не менялись больше 90 дней", "warning", "refresh")
            )
        if not alerts:
            self.hero_title.configure(text="Всё под контролем")
            self.hero_subtitle.configure(
                text="Активных угроз не обнаружено. Хорошее время сделать резервную копию."
            )
        else:
            self.hero_title.configure(text="Что требует внимания")
            self.hero_subtitle.configure(
                text="Эти задачи стоит закрыть в ближайшее время — кликните, чтобы перейти."
            )
        self._render_alerts(alerts)
        self._render_checklist(len(employees), len(passwords), pending)
        self._render_events(audit[:8])

    def _set_hero_loading(self) -> None:
        self.hero_title.configure(text="Загружаю данные…")
        self.hero_subtitle.configure(text=" ")
        for child in self.hero_alerts.winfo_children():
            child.destroy()

    def _render_alerts(self, alerts: Iterable[tuple[str, str, str]]) -> None:
        for child in self.hero_alerts.winfo_children():
            child.destroy()
        alerts = list(alerts)
        if not alerts:
            empty = ctk.CTkFrame(
                self.hero_alerts,
                fg_color=theme.palette_pair("success_soft"),
                corner_radius=theme.RADIUS.md,
            )
            empty.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(empty, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)
            ctk.CTkLabel(
                inner,
                text="",
                image=load_icon("check", 18, "success"),
                fg_color="transparent",
            ).pack(side="left")
            ctk.CTkLabel(
                inner,
                text="Активных алертов нет",
                text_color=theme.palette_pair("success"),
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="transparent",
            ).pack(side="left", padx=(10, 0))
            return

        for text, tone, icon_name in alerts:
            row = ctk.CTkFrame(
                self.hero_alerts,
                fg_color=theme.palette_pair(f"{tone}_soft"),
                corner_radius=theme.RADIUS.md,
            )
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)
            ctk.CTkLabel(
                inner,
                text="",
                image=load_icon(icon_name, 18, tone),
                fg_color="transparent",
            ).pack(side="left")
            ctk.CTkLabel(
                inner,
                text=text,
                text_color=theme.palette_pair(tone),
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="transparent",
                anchor="w",
            ).pack(side="left", padx=(10, 0), fill="x", expand=True)

    def _render_checklist(self, employees_count: int, passwords_count: int, pending: int) -> None:
        for child in self.checklist_body.winfo_children():
            child.destroy()
        steps = [
            ("Сервер запущен и доступен", self.app.state_obj.server_online),
            ("Создан первый отдел", employees_count > 0 or self.app.state_obj.is_done("department")),
            (
                "Добавлен хотя бы один сотрудник",
                employees_count > 0,
            ),
            (
                "Сохранена первая запись пароля",
                passwords_count > 0,
            ),
        ]
        done = sum(1 for _, ok in steps if ok)
        self.checklist_progress.configure(text=f"{done} из {len(steps)}")
        for text, ok in steps:
            row = ctk.CTkFrame(self.checklist_body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            bullet = ctk.CTkFrame(
                row,
                width=22,
                height=22,
                corner_radius=11,
                fg_color=theme.palette_pair("success" if ok else "surface_hi"),
            )
            bullet.pack(side="left")
            bullet.pack_propagate(False)
            if ok:
                ctk.CTkLabel(
                    bullet,
                    text="",
                    image=load_icon("check", 14, "on_primary"),
                    fg_color="transparent",
                ).pack(expand=True)
            ctk.CTkLabel(
                row,
                text=text,
                text_color=theme.palette_pair("text" if ok else "text_soft"),
                font=ctk.CTkFont(
                    family="Segoe UI",
                    size=13,
                    weight="bold" if ok else "normal",
                ),
                fg_color="transparent",
                anchor="w",
            ).pack(side="left", padx=(12, 0), fill="x", expand=True)
        if pending:
            ctk.CTkLabel(
                self.checklist_body,
                text=f"Ещё {pending} сотрудник{'ов' if pending != 1 else ''} ожидают ключ активации.",
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color="transparent",
                anchor="w",
            ).pack(fill="x", pady=(10, 0))

    def _render_events(self, events: list[dict]) -> None:
        for child in self.events_body.winfo_children():
            child.destroy()
        if not events:
            ctk.CTkLabel(
                self.events_body,
                text="Здесь будут отображаться действия пользователей.",
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="transparent",
                anchor="w",
                wraplength=320,
                justify="left",
            ).pack(anchor="w")
            return
        for event in events:
            label, tone = _EVENT_LABELS.get(event.get("event_type", ""), ("Событие", "info"))
            row = ctk.CTkFrame(self.events_body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            dot = ctk.CTkFrame(
                row,
                width=10,
                height=10,
                corner_radius=5,
                fg_color=theme.palette_pair(tone),
            )
            dot.pack(side="left", padx=(2, 10), pady=(8, 0))
            dot.pack_propagate(False)
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                text,
                text=label,
                text_color=theme.palette_pair("text"),
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="transparent",
                anchor="w",
            ).pack(fill="x", anchor="w")
            actor = event.get("actor_name") or event.get("actor_username") or "Система"
            when = _format_time(event.get("created_at", ""))
            ctk.CTkLabel(
                text,
                text=f"{actor} · {when}",
                text_color=theme.palette_pair("text_muted"),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color="transparent",
                anchor="w",
            ).pack(fill="x", anchor="w")

    def _switch_tab(self, key: str) -> None:
        page = self.app._pages.get("dashboard")
        if page and hasattr(page, "tabs"):
            page.tabs.activate(key)

    def _open_tutorial(self) -> None:
        from ..dialogs.onboarding import start_onboarding
        start_onboarding(self.app)


def _is_weak(password: str) -> bool:
    if not password or len(password) < 10:
        return True
    classes = sum(
        [
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(not c.isalnum() for c in password),
        ]
    )
    return classes < 3


def _is_stale(timestamp: str) -> bool:
    seconds = seconds_since(timestamp)
    if seconds is None:
        return False
    return seconds > 90 * 86400


def _is_today(timestamp: str) -> bool:
    seconds = seconds_since(timestamp)
    if seconds is None:
        return False
    return seconds <= 86400

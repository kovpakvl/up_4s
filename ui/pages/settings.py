"""Страница "Настройки": внешний вид, сервер, безопасность, обучение, выход."""
from __future__ import annotations

import customtkinter as ctk

import threading

from admin_api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.button import DangerButton, GhostButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card
from ..widgets.field import LabeledEntry
from .base import Page


class SettingsPage(Page):
    title = "Настройки"
    subtitle = "Сервер, безопасность и внешний вид приложения"

    def __init__(self, master, app):
        super().__init__(master, app)

        wrap = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme.palette_pair("line_strong"),
        )
        wrap.pack(fill="both", expand=True, padx=24, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=1)

        # профиль администратора
        self.profile_card = Card(wrap)
        self.profile_card.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 16))
        self._build_profile(self.profile_card)

        # внешний вид
        self.appearance_card = Card(wrap)
        self.appearance_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        self._build_appearance(self.appearance_card)

        # сервер
        self.server_card = Card(wrap)
        self.server_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        self._build_server(self.server_card)

        # ссылки для сотрудников
        self.links_card = Card(wrap)
        self.links_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 16))
        self._build_links(self.links_card)

        # обучение
        self.tutor_card = Card(wrap)
        self.tutor_card.grid(row=3, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        self._build_tutorial(self.tutor_card)

        # опасная зона
        self.danger_card = Card(wrap)
        self.danger_card.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        self._build_danger(self.danger_card)

        self.after(150, self._refresh_server_state)
        self.after(150, self._load_profile)

    # ─── секции ───────────────────────────────────────────────────────
    def _section_header(self, parent: ctk.CTkFrame, title: str, subtitle: str, icon: str) -> None:
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.pack(fill="x", padx=22, pady=(22, 4))
        bubble = ctk.CTkFrame(
            head, width=38, height=38, corner_radius=12, fg_color=theme.palette_pair("primary_soft")
        )
        bubble.pack(side="left")
        bubble.pack_propagate(False)
        ctk.CTkLabel(
            bubble, text="", image=load_icon(icon, 20, "primary"), fg_color="transparent"
        ).pack(expand=True)
        text = ctk.CTkFrame(head, fg_color="transparent")
        text.pack(side="left", padx=(12, 0), fill="x", expand=True)
        ctk.CTkLabel(
            text,
            text=title,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="transparent",
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            text,
            text=subtitle,
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            anchor="w",
        ).pack(anchor="w")

    def _build_profile(self, card: ctk.CTkFrame) -> None:
        self._section_header(
            card,
            "Профиль администратора",
            "Имя, которое видят сотрудники и журналы событий",
            "user",
        )
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=(14, 22))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.profile_display = LabeledEntry(
            body, label="Отображаемое имя *", placeholder="Анна Иванова"
        )
        self.profile_display.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))

        self.profile_username = LabeledEntry(
            body, label="Логин (нельзя изменить)", placeholder=""
        )
        self.profile_username.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.profile_username.entry.configure(state="readonly")

        self.profile_status = ctk.CTkLabel(
            body,
            text=" ",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            anchor="w",
        )
        self.profile_status.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))

        PrimaryButton(
            body, text="Сохранить", icon="check", command=self._save_profile
        ).grid(row=2, column=0, sticky="w")

    def _build_appearance(self, card: ctk.CTkFrame) -> None:
        self._section_header(
            card,
            "Внешний вид",
            "Переключение между тёмной и светлой темой",
            "sun" if theme.is_dark() else "moon",
        )
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=(14, 22))

        toggle = ctk.CTkSegmentedButton(
            body,
            values=["Тёмная", "Светлая"],
            selected_color=theme.palette_pair("primary"),
            selected_hover_color=theme.palette_pair("primary_hover"),
            unselected_color=theme.palette_pair("surface_soft"),
            unselected_hover_color=theme.palette_pair("surface_hi"),
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_theme_select,
        )
        toggle.set("Тёмная" if theme.is_dark() else "Светлая")
        toggle.pack(fill="x")

    def _build_server(self, card: ctk.CTkFrame) -> None:
        self._section_header(
            card,
            "Сервер SecureOffice",
            "Управление контейнерами Docker Compose",
            "power",
        )
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=(14, 22))

        self.server_status_label = ctk.CTkLabel(
            body,
            text="Проверяю статус…",
            text_color=theme.palette_pair("text_soft"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            anchor="w",
        )
        self.server_status_label.pack(fill="x", anchor="w", pady=(0, 12))

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        PrimaryButton(
            row, text="Запустить", icon="power", command=self._start_server
        ).pack(side="left")
        SecondaryButton(
            row,
            text="Проверить",
            icon="refresh",
            command=self._refresh_server_state,
        ).pack(side="left", padx=(8, 0))
        GhostButton(
            row,
            text="Остановить",
            icon="close",
            command=self._stop_server,
        ).pack(side="left", padx=(8, 0))

    def _build_links(self, card: ctk.CTkFrame) -> None:
        self._section_header(
            card,
            "Ссылка для сотрудников",
            "Адрес страницы входа в кабинет сотрудника",
            "mail",
        )
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=(14, 22))
        body.grid_columnconfigure(0, weight=1)

        self.app.state_obj.update_urls()
        self.login_var = ctk.StringVar(value=self.app.state_obj.login_url or "")

        ctk.CTkLabel(
            body,
            text="Ссылка для входа",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="transparent",
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        entry_row = ctk.CTkFrame(body, fg_color="transparent")
        entry_row.grid(row=1, column=0, sticky="ew")
        entry_row.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(
            entry_row,
            textvariable=self.login_var,
            fg_color=theme.palette_pair("surface_soft"),
            text_color=theme.palette_pair("text"),
            border_color=theme.palette_pair("line"),
            border_width=1,
            corner_radius=theme.RADIUS.md,
            height=40,
        )
        entry.grid(row=0, column=0, sticky="ew")
        entry.configure(state="readonly")
        SecondaryButton(
            entry_row,
            text="Копировать",
            icon="copy",
            command=lambda: self._copy(self.login_var.get(), "Скопировано"),
        ).grid(row=0, column=1, padx=(8, 0))

    def _build_tutorial(self, card: ctk.CTkFrame) -> None:
        self._section_header(
            card,
            "Обучение",
            "Краткий тур по разделам приложения",
            "help",
        )
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=(14, 22))
        ctk.CTkLabel(
            body,
            text="Запустите пошаговое обучение — мы покажем основные действия в реальных разделах.",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        PrimaryButton(
            body, text="Открыть обучение", icon="sparkles", command=self._open_tutorial
        ).pack(anchor="w")

    def _build_danger(self, card: ctk.CTkFrame) -> None:
        self._section_header(
            card,
            "Безопасность",
            "Завершение сеанса и работа с локальным хранилищем",
            "lock",
        )
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=(14, 22))
        ctk.CTkLabel(
            body,
            text=f"Текущий админ: {self.app.state_obj.user.get('display_name', '—')}",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
        ).pack(anchor="w", pady=(0, 12))
        DangerButton(
            body, text="Выйти", icon="logout", command=self.app._logout
        ).pack(fill="x")

    # ─── actions ──────────────────────────────────────────────────────
    def _on_theme_select(self, value: str) -> None:
        theme.set_theme("dark" if value == "Тёмная" else "light")

    def _start_server(self) -> None:
        self.server_status_label.configure(text="Запускаю контейнеры…")

        def on_done(output: str, error) -> None:
            if error:
                self.app.toasts.show(f"Не удалось запустить: {error}", tone="danger")
                self.server_status_label.configure(text=str(error))
                return
            self.app.toasts.show("Сервер запущен", tone="success")
            self._refresh_server_state()

        self.app.start_server_async(on_done)

    def _stop_server(self) -> None:
        from ..dialogs.confirm import confirm
        confirm(
            self.app,
            title="Остановить сервер?",
            message="Сотрудники потеряют доступ к веб-кабинету, пока сервер не будет запущен снова.",
            confirm_text="Остановить",
            tone="warning",
            icon="close",
            on_confirm=self._do_stop_server,
        )

    def _do_stop_server(self) -> None:
        self.server_status_label.configure(text="Останавливаю контейнеры…")
        import threading
        from admin_server_control import ServerCommandError

        def worker() -> None:
            try:
                self.app.state_obj.server.stop()
            except ServerCommandError as exc:
                self.after(0, lambda e=str(exc): self.server_status_label.configure(text=e))
                return
            self.after(0, self._refresh_server_state)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_server_state(self) -> None:
        def on_done(error) -> None:
            if error:
                self.server_status_label.configure(
                    text=f"Сервер не отвечает: {error}",
                )
                return
            self.server_status_label.configure(
                text=(
                    "Сервер работает. Администратор создан."
                    if self.app.state_obj.admin_initialized
                    else "Сервер работает. Первый администратор ещё не создан."
                )
            )

        self.app.refresh_status_async(on_done)

    def _copy(self, value: str, label: str) -> None:
        if not value:
            self.app.toasts.show("Нет адреса для копирования", tone="warning")
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(value)
        self.app.toasts.show(label, tone="success")

    def _open_tutorial(self) -> None:
        from ..dialogs.onboarding import start_onboarding
        start_onboarding(self.app)

    # ─── профиль ──────────────────────────────────────────────────────
    def _load_profile(self) -> None:
        if not self.app.state_obj.api.token:
            return

        def worker() -> None:
            try:
                payload = self.app.state_obj.api.me()
            except AdminApiError as exc:
                self.after(0, lambda e=str(exc): self._on_profile_error(e))
                return
            self.after(0, lambda p=payload: self._on_profile_loaded(p))

        threading.Thread(target=worker, daemon=True).start()

    def _on_profile_loaded(self, payload: dict) -> None:
        self.profile_display.set(payload.get("display_name", ""))
        self.profile_username.entry.configure(state="normal")
        self.profile_username.set(payload.get("username", ""))
        self.profile_username.entry.configure(state="readonly")

    def _on_profile_error(self, message: str) -> None:
        self.profile_status.configure(
            text=message, text_color=theme.palette_pair("danger")
        )

    def _save_profile(self) -> None:
        display = self.profile_display.get().strip()
        if not display:
            self._on_profile_error("Имя не может быть пустым.")
            return

        def worker() -> None:
            try:
                payload = self.app.state_obj.api.update_profile(display_name=display)
            except AdminApiError as exc:
                self.after(0, lambda e=str(exc): self._on_profile_error(e))
                return
            self.after(0, lambda p=payload: self._on_profile_saved(p))

        threading.Thread(target=worker, daemon=True).start()

    def _on_profile_saved(self, payload: dict) -> None:
        self.profile_status.configure(
            text="Сохранено.", text_color=theme.palette_pair("success")
        )
        # обновим имя в state и topbar
        self.app.state_obj.user["display_name"] = payload.get("display_name", "")
        self.app.state_obj.notify()
        self.app.toasts.show("Профиль обновлён", tone="success")

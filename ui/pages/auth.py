"""Экран авторизации администратора.

Состояния:
- offline:  сервер недоступен, показываем подсказку «Запустить сервер».
- setup:    сервер работает, но первого администратора ещё нет → форма создания.
- login:    стандартный вход.
"""
from __future__ import annotations

import customtkinter as ctk

from admin_api_client import AdminApiError
from admin_server_control import ServerCommandError

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.button import GhostButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card
from ..widgets.field import LabeledEntry


class AuthScreen(ctk.CTkFrame):
    def __init__(self, master, app, *, offline: bool):
        super().__init__(master, fg_color=theme.palette_pair("bg"), corner_radius=0)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, padx=24, pady=24)

        # бренд сверху
        brand = ctk.CTkFrame(center, fg_color="transparent")
        brand.pack(pady=(0, 18))
        ctk.CTkLabel(
            brand,
            text="",
            image=load_icon("shield", 36, "primary"),
            fg_color="transparent",
        ).pack(side="left", padx=(0, 12))
        text_block = ctk.CTkFrame(brand, fg_color="transparent")
        text_block.pack(side="left")
        ctk.CTkLabel(
            text_block,
            text="SecureOffice",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_block,
            text="Корпоративный менеджер доступов",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(anchor="w")

        self.card = Card(center, width=460)
        self.card.pack()
        self.card.pack_propagate(False)
        self.card.configure(height=480 if not offline else 360)

        self.error_var = ctk.StringVar(value="")
        self.error_label: ctk.CTkLabel | None = None

        if offline:
            self._render_offline()
        else:
            mode = "setup" if not app.state_obj.admin_initialized else "login"
            self._render_form(mode)

    # ─── views ──────────────────────────────────────────────────────────
    def _render_offline(self) -> None:
        for child in self.card.winfo_children():
            child.destroy()
        self.card.configure(height=380)

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=32)

        icon_circle = ctk.CTkFrame(
            inner,
            width=64,
            height=64,
            corner_radius=32,
            fg_color=theme.palette_pair("danger_soft"),
        )
        icon_circle.pack()
        icon_circle.pack_propagate(False)
        ctk.CTkLabel(
            icon_circle,
            text="",
            image=load_icon("alert", 28, "danger"),
            fg_color="transparent",
        ).pack(expand=True)

        ctk.CTkLabel(
            inner,
            text="Сервер не отвечает",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        ).pack(pady=(18, 6))
        ctk.CTkLabel(
            inner,
            text="Запустите контейнеры SecureOffice или проверьте Docker. После запуска нажмите «Проверить ещё раз».",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            wraplength=360,
            justify="center",
        ).pack(pady=(0, 18))

        PrimaryButton(
            inner,
            text="Запустить сервер",
            icon="power",
            command=self._start_server,
        ).pack(fill="x")
        SecondaryButton(
            inner,
            text="Проверить ещё раз",
            icon="refresh",
            command=self._recheck_server,
        ).pack(fill="x", pady=(10, 0))

    def _render_form(self, mode: str) -> None:
        for child in self.card.winfo_children():
            child.destroy()
        self.card.configure(height=480 if mode == "setup" else 420)

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=32)

        is_setup = mode == "setup"
        title = "Создайте первого администратора" if is_setup else "Вход в SecureOffice"
        subtitle = (
            "Это учётная запись, под которой вы будете управлять компанией."
            if is_setup
            else "Используйте логин и пароль администратора."
        )
        ctk.CTkLabel(
            inner,
            text=title,
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text=subtitle,
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(2, 18))

        self.display_field = None
        if is_setup:
            self.display_field = LabeledEntry(
                inner, label="Имя", placeholder="Например, Анна Иванова"
            )
            self.display_field.pack(fill="x", pady=(0, 12))

        self.username_field = LabeledEntry(
            inner, label="Логин", placeholder="admin"
        )
        self.username_field.pack(fill="x", pady=(0, 12))
        self.password_field = LabeledEntry(
            inner, label="Пароль", placeholder="••••••••", secret=True
        )
        self.password_field.pack(fill="x", pady=(0, 12))

        self.repeat_field = None
        if is_setup:
            self.repeat_field = LabeledEntry(
                inner, label="Повтор пароля", placeholder="••••••••", secret=True
            )
            self.repeat_field.pack(fill="x", pady=(0, 12))

        self.error_label = ctk.CTkLabel(
            inner,
            textvariable=self.error_var,
            text_color=theme.palette_pair("danger"),
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            wraplength=400,
            justify="left",
        )
        self.error_label.pack(anchor="w", pady=(2, 6))
        self.error_var.set("")

        cta_text = "Создать аккаунт" if is_setup else "Войти"
        cta = PrimaryButton(
            inner,
            text=cta_text,
            icon="arrow_right",
            command=lambda: self._submit(mode),
        )
        cta.pack(fill="x", pady=(10, 0))

        if is_setup:
            GhostButton(
                inner,
                text="Уже есть аккаунт? Войти",
                command=lambda: self._render_form("login"),
            ).pack(fill="x", pady=(8, 0))
        elif self.app.state_obj.admin_initialized is False:
            GhostButton(
                inner,
                text="Создать первого администратора",
                command=lambda: self._render_form("setup"),
            ).pack(fill="x", pady=(8, 0))

        # Enter в любом поле = submit
        for field in (
            self.display_field,
            self.username_field,
            self.password_field,
            self.repeat_field,
        ):
            if field is not None:
                field.entry.bind("<Return>", lambda _e: self._submit(mode))
        first = self.display_field or self.username_field
        first.focus()

    # ─── actions ────────────────────────────────────────────────────────
    def _start_server(self) -> None:
        self._set_error("")
        self.app.toasts.show("Запускаю сервер SecureOffice…", tone="info")

        def on_done(output, error) -> None:
            if error:
                self.app.toasts.show(f"Не удалось запустить сервер: {error}", tone="danger")
                self._set_error(error)
                return
            self._recheck_server()

        self.app.start_server_async(on_done)

    def _recheck_server(self) -> None:
        self._set_error("")
        self.app.toasts.show("Проверяю статус сервера…", tone="info")

        def on_done(error) -> None:
            if error:
                self._set_error(error)
                return
            self.app._refresh_route()

        self.app.refresh_status_async(on_done)

    def _submit(self, mode: str) -> None:
        username = self.username_field.get().strip()
        password = self.password_field.get()
        if not username or not password:
            self._set_error("Введите логин и пароль.")
            return
        if mode == "setup":
            display = self.display_field.get().strip() if self.display_field else ""
            repeat = self.repeat_field.get() if self.repeat_field else ""
            if not display:
                self._set_error("Укажите имя для аккаунта администратора.")
                return
            if len(password) < 8:
                self._set_error("Пароль должен быть не короче 8 символов.")
                return
            if password != repeat:
                self._set_error("Пароли не совпадают.")
                return
            try:
                self.app.state_obj.api.setup_admin(username, display, password)
            except AdminApiError as exc:
                self._set_error(str(exc))
                return
            try:
                self.app.state_obj.login(username, password)
            except AdminApiError as exc:
                self._set_error(str(exc))
                return
            self.app.state_obj.admin_initialized = True
            self.app.toasts.show("Аккаунт создан, добро пожаловать!", tone="success")
            self.app._refresh_route()
            # автостарт обучения сразу после создания первого админа
            self.app.after(450, lambda: self._kickoff_onboarding())
            return
        try:
            self.app.state_obj.login(username, password)
        except AdminApiError as exc:
            self._set_error(str(exc))
            return
        self.app.toasts.show(
            f"С возвращением, {self.app.state_obj.user.get('display_name', '')}!",
            tone="success",
        )
        self.app._refresh_route()

    def _kickoff_onboarding(self) -> None:
        from ..dialogs.onboarding import start_onboarding
        start_onboarding(self.app)

    def _set_error(self, message: str) -> None:
        self.error_var.set(message)

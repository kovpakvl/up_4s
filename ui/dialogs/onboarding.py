"""Сценарный wizard первого запуска.

5 шагов: сервер → отдел → сотрудник → ключ → первый пароль.
Каждый шаг — отдельная карточка с прогресс-баром, объяснением и
конкретным действием. Между шагами — плавный fade-переход.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Optional

import customtkinter as ctk

from admin_api_client import AdminApiError

from .. import theme
from ..assets.icons import icon as load_icon
from ..widgets.button import GhostButton, PrimaryButton, SecondaryButton
from ..widgets.card import Card, OutlineCard
from ..widgets.field import LabeledEntry
from .base_dialog import Dialog


@dataclass
class Step:
    key: str
    title: str
    description: str
    icon: str
    builder: Callable[["Wizard", ctk.CTkFrame], None]


class Wizard:
    def __init__(self, app):
        self.app = app
        self.dialog = Dialog(
            app,
            title="Знакомство с SecureOffice",
            width=720,
            height=580,
            resizable=False,
        )
        self.steps: list[Step] = [
            Step(
                "server",
                "Проверим, что сервер на связи",
                "Без сервера сотрудники не смогут зайти в кабинет. Если что-то не так — мы поможем запустить контейнеры.",
                "power",
                _build_server_step,
            ),
            Step(
                "department",
                "Создайте первый отдел",
                "Отделы помогают группировать сотрудников и пароли. Можно начать с одного, потом добавить ещё.",
                "building",
                _build_department_step,
            ),
            Step(
                "employee",
                "Добавьте первого сотрудника",
                "После добавления мы сразу сгенерируем для него ключ и QR-код. Это лучшее место, чтобы попробовать flow.",
                "users",
                _build_employee_step,
            ),
            Step(
                "key",
                "Передайте ключ человеку",
                "Скопируйте инструкцию, ссылку или QR — сотрудник перейдёт на страницу активации и заведёт пароль.",
                "key",
                _build_key_step,
            ),
            Step(
                "password",
                "Сохраните первый пароль",
                "Запись пароля привязывается к сотруднику. Он увидит её в своём веб-кабинете сразу после активации.",
                "sparkles",
                _build_password_step,
            ),
        ]
        self.current_index = 0
        self.last_key_payload: Optional[dict] = None
        self.last_employee: Optional[dict] = None

        self._build_chrome()
        self._render_step()

    # ─── chrome ───────────────────────────────────────────────────────
    def _build_chrome(self) -> None:
        wrap = self.dialog.body
        wrap.grid_columnconfigure(0, weight=1)

        # верхний прогресс с точками
        self.progress_frame = ctk.CTkFrame(wrap, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(0, 16))
        self.progress_dots: list[ctk.CTkFrame] = []
        for i in range(len(self.steps)):
            dot = ctk.CTkFrame(
                self.progress_frame,
                height=6,
                corner_radius=3,
                fg_color=theme.palette_pair("surface_hi"),
            )
            dot.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 6, 0))
            self.progress_dots.append(dot)

        # карточка с заголовком и описанием
        self.header_block = ctk.CTkFrame(wrap, fg_color="transparent")
        self.header_block.pack(fill="x")

        head = ctk.CTkFrame(self.header_block, fg_color="transparent")
        head.pack(fill="x")
        self.icon_bubble = ctk.CTkFrame(
            head,
            width=48,
            height=48,
            corner_radius=16,
            fg_color=theme.palette_pair("primary_soft"),
        )
        self.icon_bubble.pack(side="left")
        self.icon_bubble.pack_propagate(False)
        self.icon_label = ctk.CTkLabel(
            self.icon_bubble,
            text="",
            image=load_icon("sparkles", 24, "primary"),
            fg_color="transparent",
        )
        self.icon_label.pack(expand=True)
        title_block = ctk.CTkFrame(head, fg_color="transparent")
        title_block.pack(side="left", padx=(14, 0), fill="x", expand=True)
        self.title_label = ctk.CTkLabel(
            title_block,
            text="",
            text_color=theme.palette_pair("text"),
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            fg_color="transparent",
            anchor="w",
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(
            title_block,
            text="",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            wraplength=540,
            justify="left",
            anchor="w",
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))

        # тело шага (динамика)
        self.body_frame = ctk.CTkFrame(wrap, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, pady=(18, 0))

        # навигация
        self.back_button = GhostButton(
            self.dialog.footer,
            text="Назад",
            icon="chevron_left",
            command=self._back,
        )
        self.back_button.pack(side="left")
        GhostButton(
            self.dialog.footer,
            text="Пропустить обучение",
            command=self.dialog.destroy,
        ).pack(side="left", padx=(8, 0))

        self.next_button = PrimaryButton(
            self.dialog.footer,
            text="Дальше",
            icon="arrow_right",
            command=self._next,
        )
        self.next_button.pack(side="right")

    # ─── render ───────────────────────────────────────────────────────
    def _render_step(self) -> None:
        step = self.steps[self.current_index]
        for child in self.body_frame.winfo_children():
            child.destroy()
        self.title_label.configure(text=step.title)
        self.subtitle_label.configure(text=step.description)
        self.icon_label.configure(image=load_icon(step.icon, 24, "primary"))
        self._sync_progress()
        step.builder(self, self.body_frame)
        self._update_nav()

    def _sync_progress(self) -> None:
        for i, dot in enumerate(self.progress_dots):
            if i < self.current_index:
                dot.configure(fg_color=theme.palette_pair("primary"))
            elif i == self.current_index:
                dot.configure(fg_color=theme.palette_pair("primary"))
            else:
                dot.configure(fg_color=theme.palette_pair("surface_hi"))

    def _update_nav(self) -> None:
        self.back_button.configure(state="normal" if self.current_index > 0 else "disabled")
        if self.current_index == len(self.steps) - 1:
            self.next_button.configure(text="  Завершить")
        else:
            self.next_button.configure(text="  Дальше")

    def _next(self) -> None:
        if self.current_index >= len(self.steps) - 1:
            self.dialog.destroy()
            self.app.toasts.show("Обучение завершено. Удачи!", tone="success")
            return
        self.current_index += 1
        self._animate_swap()

    def _back(self) -> None:
        if self.current_index == 0:
            return
        self.current_index -= 1
        self._animate_swap()

    def _animate_swap(self) -> None:
        """Простая анимация: затемнить → перерисовать."""
        self.body_frame.configure(fg_color=theme.palette_pair("surface_soft"))
        self.dialog.after(60, self._do_swap)

    def _do_swap(self) -> None:
        self.body_frame.configure(fg_color="transparent")
        self._render_step()


# ─── строители шагов ────────────────────────────────────────────────────
def _build_server_step(wizard: Wizard, parent: ctk.CTkFrame) -> None:
    state = ctk.StringVar(value="Проверяю статус сервера…")
    badge = ctk.CTkLabel(
        parent,
        textvariable=state,
        text_color=theme.palette_pair("text_soft"),
        font=ctk.CTkFont(family="Segoe UI", size=13),
        fg_color="transparent",
    )
    badge.pack(anchor="w")

    actions = ctk.CTkFrame(parent, fg_color="transparent")
    actions.pack(anchor="w", pady=(14, 0))

    def render_status() -> None:
        if wizard.app.state_obj.server_online:
            state.set("Сервер на связи. Можно идти дальше.")
        else:
            state.set("Сервер пока не отвечает. Запустите контейнеры или попробуйте ещё раз.")

    def do_check() -> None:
        state.set("Обновляю статус…")

        def on_done(error) -> None:
            render_status()

        wizard.app.refresh_status_async(on_done)

    def do_start() -> None:
        state.set("Запускаю Docker Compose…")

        def on_done(output: str, error) -> None:
            if error:
                state.set(f"Не получилось: {error}")
                return
            do_check()

        wizard.app.start_server_async(on_done)

    PrimaryButton(actions, text="Запустить сервер", icon="power", command=do_start).pack(side="left")
    SecondaryButton(
        actions, text="Проверить ещё раз", icon="refresh", command=do_check
    ).pack(side="left", padx=(8, 0))

    render_status()


def _build_department_step(wizard: Wizard, parent: ctk.CTkFrame) -> None:
    field = LabeledEntry(parent, label="Название отдела", placeholder="Например, IT")
    field.pack(fill="x", pady=(0, 12))

    status_var = ctk.StringVar(value="")
    status_label = ctk.CTkLabel(
        parent,
        textvariable=status_var,
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color="transparent",
        anchor="w",
    )
    status_label.pack(anchor="w")

    try:
        existing = wizard.app.state_obj.api.departments()
    except AdminApiError:
        existing = []
    if existing:
        names = ", ".join(d["name"] for d in existing[:6])
        status_var.set(f"Уже добавлены: {names}")
        status_label.configure(text_color=theme.palette_pair("success"))

    def create() -> None:
        name = field.get().strip()
        if not name:
            status_var.set("Введите название отдела.")
            status_label.configure(text_color=theme.palette_pair("danger"))
            return
        try:
            wizard.app.state_obj.api.create_department(name)
        except AdminApiError as exc:
            status_var.set(str(exc))
            status_label.configure(text_color=theme.palette_pair("danger"))
            return
        status_var.set(f"Отдел «{name}» создан. Идём дальше.")
        status_label.configure(text_color=theme.palette_pair("success"))
        wizard.app.state_obj.mark_done("department")
        field.set("")

    PrimaryButton(parent, text="Создать отдел", icon="plus", command=create).pack(
        anchor="w", pady=(14, 0)
    )


def _build_employee_step(wizard: Wizard, parent: ctk.CTkFrame) -> None:
    name_field = LabeledEntry(parent, label="ФИО", placeholder="Анна Иванова")
    name_field.pack(fill="x", pady=(0, 12))
    email_field = LabeledEntry(parent, label="Email", placeholder="anna@example.com")
    email_field.pack(fill="x", pady=(0, 12))

    status_var = ctk.StringVar(value="")
    status_label = ctk.CTkLabel(
        parent,
        textvariable=status_var,
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color="transparent",
        anchor="w",
    )
    status_label.pack(anchor="w", pady=(0, 8))

    def create() -> None:
        name = name_field.get().strip()
        if not name:
            status_var.set("Введите ФИО.")
            status_label.configure(text_color=theme.palette_pair("danger"))
            return
        try:
            departments = wizard.app.state_obj.api.departments()
            dep_id = int(departments[0]["id"]) if departments else None
            employee = wizard.app.state_obj.api.create_employee(
                name,
                email_field.get().strip(),
                "",
                department_id=dep_id,
                position_id=None,
            )
            key_payload = wizard.app.state_obj.api.create_activation_key(int(employee["id"]))
        except AdminApiError as exc:
            status_var.set(str(exc))
            status_label.configure(text_color=theme.palette_pair("danger"))
            return
        wizard.last_employee = employee
        wizard.last_key_payload = key_payload
        wizard.app.state_obj.update_urls()
        status_var.set(
            f"{name} создан, ключ выпущен. На следующем шаге вы его покажете."
        )
        status_label.configure(text_color=theme.palette_pair("success"))

    PrimaryButton(
        parent, text="Создать сотрудника и ключ", icon="key", command=create
    ).pack(anchor="w")


def _build_key_step(wizard: Wizard, parent: ctk.CTkFrame) -> None:
    if not wizard.last_key_payload or not wizard.last_employee:
        ctk.CTkLabel(
            parent,
            text="Сначала создайте сотрудника на предыдущем шаге.",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
        ).pack(anchor="w")
        return
    code = wizard.last_key_payload.get("code", "")
    activation_url = wizard.app.state_obj.activation_url

    OutlineCard(parent)  # placeholder, не используем
    box = OutlineCard(parent)
    box.pack(fill="x")
    ctk.CTkLabel(
        box,
        text="Код активации",
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color="transparent",
    ).pack(anchor="w", padx=18, pady=(14, 2))
    ctk.CTkLabel(
        box,
        text=code,
        text_color=theme.palette_pair("primary"),
        font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
        fg_color="transparent",
    ).pack(anchor="w", padx=18, pady=(0, 14))

    ctk.CTkLabel(
        parent,
        text=f"Ссылка: {activation_url}",
        text_color=theme.palette_pair("text_soft"),
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color="transparent",
        anchor="w",
    ).pack(fill="x", pady=(12, 0))

    actions = ctk.CTkFrame(parent, fg_color="transparent")
    actions.pack(anchor="w", pady=(14, 0))

    def copy_code() -> None:
        wizard.app.clipboard_clear()
        wizard.app.clipboard_append(code)
        wizard.app.toasts.show("Код скопирован", tone="success")

    def open_full() -> None:
        from .activation_key import show_activation_key
        show_activation_key(
            wizard.app,
            employee=wizard.last_employee,
            code=code,
            expires_at=wizard.last_key_payload.get("expires_at", ""),
            activation_url=activation_url,
        )

    PrimaryButton(actions, text="Открыть карточку с QR", icon="qr", command=open_full).pack(
        side="left"
    )
    SecondaryButton(actions, text="Скопировать код", icon="copy", command=copy_code).pack(
        side="left", padx=(8, 0)
    )


def _build_password_step(wizard: Wizard, parent: ctk.CTkFrame) -> None:
    employee = wizard.last_employee
    if not employee:
        ctk.CTkLabel(
            parent,
            text="Создайте сотрудника на шаге 3, чтобы выдать ему первый пароль.",
            text_color=theme.palette_pair("text_muted"),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
        ).pack(anchor="w")
        return

    service_field = LabeledEntry(parent, label="Сервис", placeholder="Например, Google Workspace")
    service_field.pack(fill="x", pady=(0, 12))
    login_field = LabeledEntry(parent, label="Логин", placeholder="anna@example.com")
    login_field.pack(fill="x", pady=(0, 12))
    password_field = LabeledEntry(parent, label="Пароль", placeholder="можно сгенерировать")
    password_field.pack(fill="x", pady=(0, 8))

    status_var = ctk.StringVar(value="")
    status_label = ctk.CTkLabel(
        parent,
        textvariable=status_var,
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color="transparent",
        anchor="w",
    )
    status_label.pack(anchor="w")

    def generate() -> None:
        from password_generator import generate_password
        password_field.set(generate_password(length=20))

    def save() -> None:
        service = service_field.get().strip()
        password = password_field.get()
        if not service or not password:
            status_var.set("Введите сервис и пароль.")
            status_label.configure(text_color=theme.palette_pair("danger"))
            return
        try:
            wizard.app.state_obj.api.create_password_entries(
                employee_ids=[int(employee["id"])],
                service_name=service,
                site_url="",
                login=login_field.get().strip(),
                password=password,
                comment="",
                is_favorite=False,
            )
        except AdminApiError as exc:
            status_var.set(str(exc))
            status_label.configure(text_color=theme.palette_pair("danger"))
            return
        status_var.set("Готово. Запись появится у сотрудника после активации.")
        status_label.configure(text_color=theme.palette_pair("success"))

    actions = ctk.CTkFrame(parent, fg_color="transparent")
    actions.pack(anchor="w", pady=(14, 0))
    SecondaryButton(actions, text="Сгенерировать", icon="sparkles", command=generate).pack(
        side="left"
    )
    PrimaryButton(actions, text="Сохранить запись", icon="check", command=save).pack(
        side="left", padx=(8, 0)
    )


def start_onboarding(app) -> None:
    Wizard(app)

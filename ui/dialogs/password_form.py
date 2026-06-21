"""Форма создания/редактирования записи пароля.

Одна колонка: сначала получатели (кому привязать запись), потом сами поля.
Так читается естественно сверху вниз, и блок «Кому» не пропадает в узких
окнах.
"""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from desktop.api_client import AdminApiError
from desktop.password_generator import generate_password

from .. import theme
from ..widgets.button import PrimaryButton, SecondaryButton
from ..widgets.card import OutlineCard
from ..widgets.field import LabeledEntry, LabeledTextArea
from ..widgets.strength_meter import StrengthMeter
from .base_dialog import Dialog


def open_password_form(
    app,
    *,
    employees: list[dict],
    entry: Optional[dict] = None,
    on_done: Callable[[], None],
) -> None:
    title = "Изменить запись" if entry else "Новая запись пароля"
    dialog = Dialog(app, title=title, width=620, height=720, resizable=True)

    scroller = ctk.CTkScrollableFrame(
        dialog.body,
        fg_color="transparent",
        scrollbar_button_color=theme.palette_pair("line_strong"),
    )
    scroller.pack(fill="both", expand=True)
    scroller.grid_columnconfigure(0, weight=1)

    # ─── 1. получатели ───────────────────────────────────────────────
    holders = OutlineCard(scroller)
    holders.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    ctk.CTkLabel(
        holders,
        text="Кому выдать запись",
        text_color=theme.palette_pair("text"),
        font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        fg_color="transparent",
    ).pack(anchor="w", padx=18, pady=(16, 4))
    ctk.CTkLabel(
        holders,
        text=(
            "Запись привязана к сотруднику и редактируется отдельно."
            if entry
            else "Можно выбрать несколько сотрудников — для каждого создастся своя копия."
        ),
        text_color=theme.palette_pair("text_muted"),
        font=ctk.CTkFont(family="Segoe UI", size=11),
        wraplength=540,
        justify="left",
        fg_color="transparent",
        anchor="w",
    ).pack(fill="x", padx=18, pady=(0, 10))

    holders_inner = ctk.CTkFrame(holders, fg_color="transparent")
    holders_inner.pack(fill="x", padx=12, pady=(0, 14))
    holders_inner.grid_columnconfigure(0, weight=1)
    holders_inner.grid_columnconfigure(1, weight=1)

    employee_vars: dict[int, ctk.BooleanVar] = {}
    preselected_id = entry.get("employee_id") if entry else None

    for index, employee in enumerate(employees):
        var = ctk.BooleanVar(value=(preselected_id == int(employee["id"])))
        employee_vars[int(employee["id"])] = var
        check = ctk.CTkCheckBox(
            holders_inner,
            text=f"{employee['full_name']}  ·  {employee.get('department_name') or 'Без отдела'}",
            variable=var,
            fg_color=theme.palette_pair("primary"),
            text_color=theme.palette_pair("text"),
            border_color=theme.palette_pair("line_strong"),
            hover_color=theme.palette_pair("primary_hover"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        check.grid(
            row=index // 2,
            column=index % 2,
            sticky="w",
            padx=8,
            pady=4,
        )
        if entry:
            check.configure(state="disabled")

    if not employees:
        ctk.CTkLabel(
            holders,
            text="Сначала добавьте сотрудников в разделе «Сотрудники».",
            text_color=theme.palette_pair("warning"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 14))

    # ─── 2. поля ─────────────────────────────────────────────────────
    fields = OutlineCard(scroller)
    fields.grid(row=1, column=0, sticky="ew", pady=(0, 4))

    container = ctk.CTkFrame(fields, fg_color="transparent")
    container.pack(fill="x", padx=18, pady=18)

    service_field = LabeledEntry(container, label="Сервис *", placeholder="Например, Google Workspace")
    service_field.pack(fill="x", pady=(0, 12))
    if entry:
        service_field.set(entry.get("service_name", ""))

    url_field = LabeledEntry(container, label="URL", placeholder="https://…")
    url_field.pack(fill="x", pady=(0, 12))
    if entry:
        url_field.set(entry.get("site_url", ""))

    login_field = LabeledEntry(container, label="Логин", placeholder="admin@example.com")
    login_field.pack(fill="x", pady=(0, 12))
    if entry:
        login_field.set(entry.get("login", ""))

    password_var = ctk.StringVar(value=entry.get("password", "") if entry else "")
    pass_field = LabeledEntry(
        container,
        label="Пароль *",
        placeholder="Сгенерировать или ввести вручную",
        textvariable=password_var,
        secret=False,
    )
    pass_field.pack(fill="x", pady=(0, 6))

    meter = StrengthMeter(container)
    meter.pack(fill="x", pady=(0, 10))
    meter.update(password_var.get())

    def on_change(*_args) -> None:
        meter.update(password_var.get())

    password_var.trace_add("write", on_change)

    SecondaryButton(
        container,
        text="Сгенерировать стойкий пароль",
        icon="sparkles",
        command=lambda: password_var.set(generate_password(length=20)),
    ).pack(anchor="w", pady=(0, 14))

    comment_field = LabeledTextArea(container, label="Комментарий", height=80)
    comment_field.pack(fill="x", pady=(0, 8))
    if entry:
        comment_field.set(entry.get("comment", ""))

    favorite_var = ctk.BooleanVar(value=bool(entry.get("is_favorite")) if entry else False)
    ctk.CTkCheckBox(
        container,
        text="Избранная запись",
        variable=favorite_var,
        fg_color=theme.palette_pair("primary"),
        text_color=theme.palette_pair("text"),
        border_color=theme.palette_pair("line_strong"),
        hover_color=theme.palette_pair("primary_hover"),
    ).pack(anchor="w", pady=(6, 0))

    # ─── footer ──────────────────────────────────────────────────────
    error_var = ctk.StringVar(value="")
    error_label = ctk.CTkLabel(
        dialog.footer,
        textvariable=error_var,
        text_color=theme.palette_pair("danger"),
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        fg_color="transparent",
        anchor="w",
    )
    error_label.pack(side="left")

    def submit() -> None:
        service = service_field.get().strip()
        password = password_var.get()
        if not service:
            error_var.set("Укажите название сервиса.")
            return
        if not password:
            error_var.set("Введите пароль или сгенерируйте.")
            return

        payload = {
            "service_name": service,
            "site_url": url_field.get().strip(),
            "login": login_field.get().strip(),
            "password": password,
            "comment": comment_field.get(),
            "is_favorite": favorite_var.get(),
        }

        try:
            if entry:
                app.state_obj.api.update_password_entry(int(entry["id"]), **payload)
                app.toasts.show("Запись обновлена", tone="success")
            else:
                employee_ids = [eid for eid, var in employee_vars.items() if var.get()]
                if not employee_ids:
                    error_var.set("Выберите хотя бы одного сотрудника.")
                    return
                created = app.state_obj.api.create_password_entries(
                    employee_ids=employee_ids, **payload
                )
                app.toasts.show(
                    f"Создано записей: {len(created)}", tone="success"
                )
        except AdminApiError as exc:
            error_var.set(str(exc))
            return

        dialog.destroy()
        on_done()

    PrimaryButton(
        dialog.footer,
        text="Сохранить",
        icon="check",
        command=submit,
    ).pack(side="right")
    SecondaryButton(dialog.footer, text="Отмена", command=dialog.destroy).pack(
        side="right", padx=(0, 8)
    )

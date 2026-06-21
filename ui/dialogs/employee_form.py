"""Форма добавления сотрудника."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from admin_api_client import AdminApiError

from .. import theme
from ..widgets.button import PrimaryButton, SecondaryButton
from ..widgets.field import LabeledEntry, LabeledOptionMenu
from .base_dialog import Dialog


def open_employee_form(
    app,
    departments: list[dict],
    on_created: Callable[[dict, dict], None],
) -> None:
    dialog = Dialog(app, title="Новый сотрудник", width=520, height=560)

    name_field = LabeledEntry(dialog.body, label="ФИО *", placeholder="Анна Иванова")
    name_field.pack(fill="x", pady=(0, 12))
    name_field.focus()

    email_field = LabeledEntry(dialog.body, label="Email", placeholder="anna@example.com")
    email_field.pack(fill="x", pady=(0, 12))

    phone_field = LabeledEntry(dialog.body, label="Телефон", placeholder="+7 …")
    phone_field.pack(fill="x", pady=(0, 12))

    dep_labels = ["Без отдела"] + [d["name"] for d in departments]
    dep_field = LabeledOptionMenu(dialog.body, label="Отдел", values=dep_labels)
    dep_field.pack(fill="x", pady=(0, 12))

    pos_field = LabeledOptionMenu(
        dialog.body, label="Должность", values=["Без должности"]
    )
    pos_field.pack(fill="x", pady=(0, 12))

    def refresh_positions(*_args) -> None:
        dep_name = dep_field.get()
        positions = ["Без должности"]
        for d in departments:
            if d["name"] == dep_name:
                positions += [p["name"] for p in d.get("positions", [])]
                break
        pos_field.configure_values(positions)
        pos_field.set("Без должности")

    dep_field.menu.configure(command=refresh_positions)

    error_var = ctk.StringVar(value="")
    error_label = ctk.CTkLabel(
        dialog.body,
        textvariable=error_var,
        text_color=theme.palette_pair("danger"),
        fg_color="transparent",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        anchor="w",
    )
    error_label.pack(fill="x", anchor="w", pady=(4, 0))

    def submit() -> None:
        name = name_field.get().strip()
        if not name:
            error_var.set("Введите ФИО сотрудника.")
            return
        dep_name = dep_field.get()
        dep_id = None
        positions = []
        for d in departments:
            if d["name"] == dep_name:
                dep_id = int(d["id"])
                positions = d.get("positions", [])
                break
        pos_id = None
        pos_label = pos_field.get()
        for p in positions:
            if p["name"] == pos_label:
                pos_id = int(p["id"])
                break

        try:
            employee = app.state_obj.api.create_employee(
                name,
                email_field.get().strip(),
                phone_field.get().strip(),
                department_id=dep_id,
                position_id=pos_id,
            )
            key_payload = app.state_obj.api.create_activation_key(int(employee["id"]))
        except AdminApiError as exc:
            error_var.set(str(exc))
            return

        dialog.destroy()
        app.toasts.show(f"Сотрудник {name} добавлен", tone="success")
        on_created(employee, key_payload)

    PrimaryButton(
        dialog.footer,
        text="Создать и выдать ключ",
        icon="key",
        command=submit,
    ).pack(side="right")
    SecondaryButton(dialog.footer, text="Отмена", command=dialog.destroy).pack(
        side="right", padx=(0, 8)
    )

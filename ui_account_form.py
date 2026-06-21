import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
from urllib.parse import urlparse

from password_generator import generate_password
from secureoffice_service import BusinessAccount, is_weak_password
from ui_theme import COLORS, apply_theme, style_text_widget


class AccountForm(tk.Toplevel):
    def __init__(
        self,
        parent,
        employees: list[dict],
        departments: list[dict],
        service_types: list[dict],
        account: Optional[dict] = None,
        selected_employee_id: Optional[int] = None,
        default_length: int = 16,
    ):
        super().__init__(parent)
        self.title("Редактирование аккаунта" if account else "Новый аккаунт")
        self.resizable(False, False)
        apply_theme(self)
        self.result: Optional[BusinessAccount] = None
        self.password_changed = False
        self._account_id = account["id"] if account else None
        self._original_password = account["password"] if account else ""
        self._default_length = default_length

        self._employees = {
            f"{item['full_name']} · {item['department_name']} [#{item['id']}]": item
            for item in employees
        }
        self._departments = {item["name"]: item["id"] for item in departments}
        self._service_types = {item["name"]: item["id"] for item in service_types}

        selected_employee = next(
            (
                item
                for item in employees
                if item["id"]
                == (account["employee_id"] if account else selected_employee_id)
            ),
            employees[0] if employees else None,
        )
        selected_department = next(
            (
                item["name"]
                for item in departments
                if item["id"]
                == (
                    account["department_id"]
                    if account
                    else (selected_employee["department_id"] if selected_employee else None)
                )
            ),
            departments[0]["name"] if departments else "",
        )
        selected_type = next(
            (
                item["name"]
                for item in service_types
                if account and item["id"] == account["service_type_id"]
            ),
            service_types[0]["name"] if service_types else "",
        )

        selected_employee_label = next(
            (
                label
                for label, item in self._employees.items()
                if selected_employee and item["id"] == selected_employee["id"]
            ),
            "",
        )
        self.employee_var = tk.StringVar(value=selected_employee_label)
        self.department_var = tk.StringVar(value=selected_department)
        self.service_type_var = tk.StringVar(value=selected_type)
        self.service_name_var = tk.StringVar(
            value=account["service_name"] if account else ""
        )
        self.site_var = tk.StringVar(value=account["site_url"] if account else "")
        self.login_var = tk.StringVar(value=account["login"] if account else "")
        self.email_var = tk.StringVar(value=account["email"] if account else "")
        self.password_var = tk.StringVar(value=self._original_password)
        self.password_status_var = tk.StringVar()
        self.favorite_var = tk.BooleanVar(
            value=bool(account["is_favorite"]) if account else False
        )

        self._build_ui(account["comment"] if account else "")
        self.password_var.trace_add("write", self._update_password_status)
        self._update_password_status()
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_ui(self, comment: str) -> None:
        frame = ttk.Frame(self, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Сотрудник *").grid(row=0, column=0, sticky="w", pady=5)
        employee_box = ttk.Combobox(
            frame,
            textvariable=self.employee_var,
            values=list(self._employees),
            state="readonly",
            width=39,
        )
        employee_box.grid(row=0, column=1, sticky="ew", pady=5)
        employee_box.bind("<<ComboboxSelected>>", self._sync_department)

        ttk.Label(frame, text="Отдел *").grid(row=1, column=0, sticky="w", pady=5)
        department_box = ttk.Combobox(
            frame,
            textvariable=self.department_var,
            values=list(self._departments),
            state="disabled",
            width=39,
        )
        department_box.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Тип сервиса *").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Combobox(
            frame,
            textvariable=self.service_type_var,
            values=list(self._service_types),
            state="readonly",
            width=39,
        ).grid(row=2, column=1, sticky="ew", pady=5)

        fields = [
            ("Название сервиса *", self.service_name_var),
            ("Сайт", self.site_var),
            ("Логин", self.login_var),
            ("Email", self.email_var),
        ]
        for row, (label, variable) in enumerate(fields, start=3):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, textvariable=variable, width=42)
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            if row == 3:
                entry.focus_set()

        ttk.Label(frame, text="Пароль *").grid(row=7, column=0, sticky="w", pady=5)
        password_row = ttk.Frame(frame)
        password_row.grid(row=7, column=1, sticky="ew", pady=5)
        self.password_entry = ttk.Entry(
            password_row, textvariable=self.password_var, show="*", width=29
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(password_row, text="Показать", command=self._toggle_password).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(password_row, text="Создать", command=self._generate).pack(
            side="left", padx=(6, 0)
        )
        self.password_status = ttk.Label(
            frame, textvariable=self.password_status_var
        )
        self.password_status.grid(row=8, column=1, sticky="w", pady=(0, 5))

        ttk.Label(frame, text="Комментарий").grid(row=9, column=0, sticky="nw", pady=5)
        self.comment_text = tk.Text(frame, width=42, height=5, wrap="word")
        style_text_widget(self.comment_text)
        self.comment_text.insert("1.0", comment)
        self.comment_text.grid(row=9, column=1, sticky="ew", pady=5)

        ttk.Checkbutton(
            frame, text="Избранный аккаунт", variable=self.favorite_var
        ).grid(row=10, column=1, sticky="w", pady=5)

        buttons = ttk.Frame(frame)
        buttons.grid(row=11, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(
            buttons, text="Сохранить", command=self._save, style="Accent.TButton"
        ).pack(
            side="right", padx=(0, 8)
        )

    def _sync_department(self, _event=None) -> None:
        employee = self._employees.get(self.employee_var.get())
        if not employee:
            return
        for name, department_id in self._departments.items():
            if department_id == employee["department_id"]:
                self.department_var.set(name)
                return

    def _toggle_password(self) -> None:
        self.password_entry.configure(
            show="" if self.password_entry.cget("show") == "*" else "*"
        )

    def _generate(self) -> None:
        try:
            self.password_var.set(generate_password(length=self._default_length))
        except ValueError as exc:
            messagebox.showerror("Генератор", str(exc), parent=self)

    def _update_password_status(self, *_args) -> None:
        password = self.password_var.get()
        if not password:
            text, color = "Пароль не задан", COLORS["muted"]
        elif is_weak_password(password):
            text, color = "Слабый пароль: увеличьте длину и разнообразие символов", COLORS["warning"]
        else:
            text, color = "Надёжный пароль", COLORS["accent"]
        self.password_status_var.set(text)
        if hasattr(self, "password_status"):
            self.password_status.configure(foreground=color)

    def _save(self) -> None:
        employee = self._employees.get(self.employee_var.get())
        department_id = self._departments.get(self.department_var.get())
        service_type_id = self._service_types.get(self.service_type_var.get())
        service_name = self.service_name_var.get().strip()
        login = self.login_var.get().strip()
        email = self.email_var.get().strip()
        password = self.password_var.get()
        site_url = self.site_var.get().strip()

        if employee is None or department_id is None or service_type_id is None:
            messagebox.showerror(
                "Проверка", "Выберите сотрудника, отдел и тип сервиса.", parent=self
            )
            return
        if employee["department_id"] != department_id:
            messagebox.showerror(
                "Проверка",
                "Отдел аккаунта должен совпадать с отделом сотрудника.",
                parent=self,
            )
            return
        if not service_name:
            messagebox.showerror("Проверка", "Введите название сервиса.", parent=self)
            return
        if not login and not email:
            messagebox.showerror("Проверка", "Введите логин или email.", parent=self)
            return
        if not password:
            messagebox.showerror("Проверка", "Введите пароль.", parent=self)
            return
        if email and ("@" not in email or email.startswith("@") or email.endswith("@")):
            messagebox.showerror("Проверка", "Введите корректный email.", parent=self)
            return
        if site_url and "://" not in site_url:
            site_url = f"https://{site_url}"
        if site_url:
            parsed = urlparse(site_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                messagebox.showerror(
                    "Проверка", "Введите корректный адрес сайта.", parent=self
                )
                return

        self.password_changed = password != self._original_password
        self.result = BusinessAccount(
            id=self._account_id,
            employee_id=employee["id"],
            department_id=department_id,
            service_type_id=service_type_id,
            service_name=service_name,
            site_url=site_url,
            login=login,
            password=password,
            email=email,
            comment=self.comment_text.get("1.0", "end").strip(),
            is_favorite=self.favorite_var.get(),
        )
        self.destroy()

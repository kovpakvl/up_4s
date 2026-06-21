import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from config import EMPLOYEE_ROLES, EMPLOYEE_STATUSES
from employee_service import Employee
from ui_theme import apply_theme


class EmployeeForm(tk.Toplevel):
    def __init__(self, parent, departments: list[dict], employee: Optional[dict] = None):
        super().__init__(parent)
        self.title("Редактирование сотрудника" if employee else "Новый сотрудник")
        self.resizable(False, False)
        apply_theme(self)
        self.result: Optional[Employee] = None
        self._employee_id = employee["id"] if employee else None
        self._department_by_name = {item["name"]: item["id"] for item in departments}

        self.full_name_var = tk.StringVar(value=employee["full_name"] if employee else "")
        self.position_var = tk.StringVar(value=employee["position"] if employee else "")
        self.role_var = tk.StringVar(
            value=employee["role"] if employee else EMPLOYEE_ROLES[-1]
        )
        self.department_var = tk.StringVar(
            value=employee["department_name"]
            if employee
            else (departments[0]["name"] if departments else "")
        )
        self.phone_var = tk.StringVar(value=employee["phone"] if employee else "")
        self.email_var = tk.StringVar(value=employee["email"] if employee else "")
        self.status_var = tk.StringVar(
            value=employee["status"] if employee else EMPLOYEE_STATUSES[0]
        )

        self._build_ui(list(self._department_by_name))
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_ui(self, department_names: list[str]) -> None:
        frame = ttk.Frame(self, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")

        fields = [
            ("ФИО *", self.full_name_var),
            ("Должность", self.position_var),
            ("Телефон", self.phone_var),
            ("Email", self.email_var),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=5)
            entry = ttk.Entry(frame, textvariable=variable, width=42)
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            if row == 0:
                entry.focus_set()

        ttk.Label(frame, text="Роль").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Combobox(
            frame,
            textvariable=self.role_var,
            values=EMPLOYEE_ROLES,
            state="readonly",
            width=39,
        ).grid(row=4, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Отдел *").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Combobox(
            frame,
            textvariable=self.department_var,
            values=department_names,
            state="readonly",
            width=39,
        ).grid(row=5, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Статус").grid(row=6, column=0, sticky="w", pady=5)
        ttk.Combobox(
            frame,
            textvariable=self.status_var,
            values=EMPLOYEE_STATUSES,
            state="readonly",
            width=39,
        ).grid(row=6, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(
            buttons, text="Сохранить", command=self._save, style="Accent.TButton"
        ).pack(
            side="right", padx=(0, 8)
        )

    def _save(self) -> None:
        full_name = self.full_name_var.get().strip()
        department_id = self._department_by_name.get(self.department_var.get())
        if not full_name:
            messagebox.showerror("Проверка", "Введите ФИО сотрудника.", parent=self)
            return
        if department_id is None:
            messagebox.showerror("Проверка", "Выберите отдел.", parent=self)
            return
        email = self.email_var.get().strip()
        if email and ("@" not in email or email.startswith("@") or email.endswith("@")):
            messagebox.showerror("Проверка", "Введите корректный email.", parent=self)
            return

        self.result = Employee(
            id=self._employee_id,
            full_name=full_name,
            position=self.position_var.get().strip(),
            role=self.role_var.get(),
            department_id=department_id,
            phone=self.phone_var.get().strip(),
            email=email,
            status=self.status_var.get(),
        )
        self.destroy()

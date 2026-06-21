import tkinter as tk
from typing import Optional
from tkinter import messagebox, ttk

from password_generator import generate_password
from password_service import PasswordEntry


class EntryForm(tk.Toplevel):
    def __init__(
        self,
        parent,
        title: str,
        entry: Optional[PasswordEntry] = None,
        default_length: int = 16,
    ):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: Optional[PasswordEntry] = None
        self._entry_id = entry.id if entry else None
        self._default_length = default_length

        self.service_var = tk.StringVar(value=entry.service_name if entry else "")
        self.site_var = tk.StringVar(value=entry.site_url if entry else "")
        self.login_var = tk.StringVar(value=entry.login if entry else "")
        self.email_var = tk.StringVar(value=entry.email if entry else "")
        self.password_var = tk.StringVar(value=entry.password if entry else "")
        self.repeat_var = tk.StringVar(value=entry.password if entry else "")
        self.category_var = tk.StringVar(value=entry.category if entry else "")
        self.favorite_var = tk.BooleanVar(value=entry.is_favorite if entry else False)

        self._build_ui(entry.comment if entry else "")
        self.transient(parent)
        self.grab_set()
        self.service_entry.focus_set()

    def _build_ui(self, comment: str) -> None:
        frame = ttk.Frame(self, padding=14)
        frame.grid(row=0, column=0, sticky="nsew")

        fields = [
            ("Сервис *", self.service_var),
            ("Сайт", self.site_var),
            ("Логин", self.login_var),
            ("Email", self.email_var),
            ("Пароль *", self.password_var),
            ("Повтор пароля *", self.repeat_var),
            ("Категория", self.category_var),
        ]
        for row, (label, var) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            show = "*" if "Пароль" in label else ""
            entry = ttk.Entry(frame, textvariable=var, width=38, show=show)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            if row == 0:
                self.service_entry = entry

        ttk.Button(frame, text="Сгенерировать", command=self._generate).grid(
            row=4, column=2, padx=(8, 0)
        )
        ttk.Checkbutton(frame, text="Избранное", variable=self.favorite_var).grid(
            row=7, column=1, sticky="w", pady=(6, 2)
        )
        ttk.Label(frame, text="Комментарий").grid(row=8, column=0, sticky="nw", pady=4)
        self.comment_text = tk.Text(frame, width=38, height=5)
        self.comment_text.insert("1.0", comment)
        self.comment_text.grid(row=8, column=1, columnspan=2, sticky="ew", pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=9, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Сохранить", command=self._save).pack(side="right", padx=(0, 8))

    def _generate(self) -> None:
        try:
            password = generate_password(length=self._default_length)
        except ValueError as exc:
            messagebox.showerror("Генератор", str(exc), parent=self)
            return
        self.password_var.set(password)
        self.repeat_var.set(password)

    def _save(self) -> None:
        service_name = self.service_var.get().strip()
        login = self.login_var.get().strip()
        email = self.email_var.get().strip()
        password = self.password_var.get()
        repeat_password = self.repeat_var.get()

        if not service_name:
            messagebox.showerror("Проверка", "Название сервиса обязательно.", parent=self)
            return
        if not login and not email:
            messagebox.showerror("Проверка", "Заполните логин или email.", parent=self)
            return
        if not password:
            messagebox.showerror("Проверка", "Пароль обязателен.", parent=self)
            return
        if password != repeat_password:
            messagebox.showerror("Проверка", "Пароли не совпадают.", parent=self)
            return

        self.result = PasswordEntry(
            id=self._entry_id,
            service_name=service_name,
            site_url=self.site_var.get().strip(),
            login=login,
            password=password,
            email=email,
            comment=self.comment_text.get("1.0", "end").strip(),
            category=self.category_var.get().strip(),
            is_favorite=self.favorite_var.get(),
        )
        self.destroy()

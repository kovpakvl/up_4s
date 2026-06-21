import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import time

import auth
from crypto_service import CryptoService
from database import has_user, reset_vault
from settings_service import SettingsService
from ui_main import MainWindow
from ui_theme import COLORS, apply_theme


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SecureOffice")
        self.resizable(False, False)
        apply_theme(self)
        self.password_var = tk.StringVar()
        self.repeat_var = tk.StringVar()
        self._mode = ""
        self._failed_attempts = 0
        self._locked_until = 0.0
        self._show_welcome()

    def _clear(self) -> None:
        self.unbind("<Return>")
        for child in self.winfo_children():
            child.destroy()

    def _panel(self) -> ttk.Frame:
        panel = ttk.Frame(self, padding=30, style="Panel.TFrame")
        panel.grid(row=0, column=0)
        ttk.Label(panel, text="SO", style="BrandMark.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 14)
        )
        ttk.Label(panel, text="SecureOffice", style="AuthTitle.TLabel").grid(
            row=1, column=0, columnspan=2
        )
        return panel

    def _show_welcome(self) -> None:
        self._clear()
        self._mode = ""
        self.password_var.set("")
        self.repeat_var.set("")
        panel = self._panel()
        ttk.Label(
            panel,
            text="Менеджер корпоративных паролей",
            style="Panel.TLabel",
            foreground=COLORS["muted"],
        ).grid(row=2, column=0, columnspan=2, pady=(3, 22))
        ttk.Button(
            panel,
            text="Создать аккаунт",
            command=self._start_create,
            style="Accent.TButton",
            width=32,
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Button(
            panel,
            text="Войти в существующий",
            command=self._start_login,
            width=32,
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Button(
            panel,
            text="Подключиться к компании",
            command=self._open_company_login,
            width=32,
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

    def _open_company_login(self) -> None:
        from ui_company_login import CompanyLoginWindow

        CompanyLoginWindow(self)

    def _start_create(self) -> None:
        if has_user() and not self._confirm_reset():
            return
        self._show_form("create")

    def _start_login(self) -> None:
        if not has_user():
            messagebox.showinfo(
                "Вход",
                "Существующее хранилище не найдено. Сначала создайте аккаунт.",
                parent=self,
            )
            return
        self._show_form("login")

    def _show_form(self, mode: str) -> None:
        self._clear()
        self._mode = mode
        self.password_var.set("")
        self.repeat_var.set("")
        panel = self._panel()
        is_create = mode == "create"
        ttk.Label(
            panel,
            text="Создание аккаунта" if is_create else "Вход в существующий аккаунт",
            style="Panel.TLabel",
            foreground=COLORS["muted"],
        ).grid(row=2, column=0, columnspan=2, pady=(3, 18))

        ttk.Label(panel, text="Мастер-пароль", style="Panel.TLabel").grid(
            row=3, column=0, sticky="w", pady=5
        )
        password_entry = ttk.Entry(
            panel, textvariable=self.password_var, show="*", width=34
        )
        password_entry.grid(row=3, column=1, pady=5, padx=(12, 0))

        next_row = 4
        if is_create:
            ttk.Label(panel, text="Повтор", style="Panel.TLabel").grid(
                row=4, column=0, sticky="w", pady=5
            )
            ttk.Entry(
                panel, textvariable=self.repeat_var, show="*", width=34
            ).grid(row=4, column=1, pady=5, padx=(12, 0))
            next_row = 5

        ttk.Button(
            panel,
            text="Создать" if is_create else "Войти",
            command=self._submit,
            style="Accent.TButton",
        ).grid(row=next_row, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        ttk.Button(panel, text="Назад", command=self._show_welcome).grid(
            row=next_row + 1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )
        if not is_create:
            ttk.Button(
                panel,
                text="Забыли мастер-пароль?",
                command=self._forgot_password,
                style="Danger.TButton",
            ).grid(
                row=next_row + 2,
                column=0,
                columnspan=2,
                sticky="ew",
                pady=(8, 0),
            )

        self.bind("<Return>", lambda _event: self._submit())
        password_entry.focus_set()

    def _submit(self) -> None:
        password = self.password_var.get()
        if self._mode == "create":
            ok, error = auth.validate_new_master_password(
                password, self.repeat_var.get()
            )
            if not ok:
                messagebox.showerror("Мастер-пароль", error, parent=self)
                return
            salt = auth.create_user(password)
        elif self._mode == "login":
            remaining = int(self._locked_until - time.monotonic())
            if remaining > 0:
                messagebox.showwarning(
                    "Вход",
                    f"Слишком много неудачных попыток. Повторите через {remaining + 1} сек.",
                    parent=self,
                )
                return
            salt = auth.verify_master_password(password)
            if salt is None:
                self._failed_attempts += 1
                if self._failed_attempts >= 5:
                    self._failed_attempts = 0
                    self._locked_until = time.monotonic() + 30
                    messagebox.showwarning(
                        "Вход",
                        "Вход временно заблокирован на 30 секунд.",
                        parent=self,
                    )
                    return
                messagebox.showerror("Вход", "Неверный мастер-пароль.", parent=self)
                return
            self._failed_attempts = 0
            self._locked_until = 0.0
        else:
            return

        crypto = CryptoService(password, salt)
        settings = SettingsService()
        settings.ensure_defaults()
        self.withdraw()
        MainWindow(self, crypto, settings)

    def _confirm_reset(self) -> bool:
        confirmation = simpledialog.askstring(
            "Новое хранилище",
            "Аккаунт уже существует. Его сотрудники и пароли будут удалены.\n"
            "Введите RESET для подтверждения:",
            parent=self,
        )
        if confirmation != "RESET":
            return False
        if not messagebox.askyesno(
            "Новое хранилище",
            "Удалить текущее хранилище без возможности восстановления?",
            parent=self,
        ):
            return False
        try:
            backup_path = SettingsService().create_backup()
        except OSError as exc:
            messagebox.showerror(
                "Новое хранилище",
                f"Не удалось создать резервную копию:\n{exc}\n\nСброс отменён.",
                parent=self,
            )
            return False
        reset_vault()
        messagebox.showinfo(
            "Резервная копия",
            f"Перед сбросом создана резервная копия:\n{backup_path}",
            parent=self,
        )
        return True

    def _forgot_password(self) -> None:
        if self._confirm_reset():
            self._show_form("create")

    def show_again(self) -> None:
        self.deiconify()
        self._show_welcome()

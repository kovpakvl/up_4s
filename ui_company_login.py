import tkinter as tk
from tkinter import messagebox, ttk

from company_client import CompanyApiError, CompanyClient
from settings_service import SettingsService
from ui_main import MainWindow
from ui_theme import COLORS, apply_theme


class CompanyLoginWindow(tk.Toplevel):
    def __init__(self, local_login):
        super().__init__(local_login)
        self.local_login = local_login
        self.title("Подключение к компании")
        self.resizable(False, False)
        apply_theme(self)
        self.server_var = tk.StringVar(value="http://127.0.0.1:8765")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.repeat_var = tk.StringVar()
        self.full_name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.invite_var = tk.StringVar()
        self.mode = "login"
        self._show_connection()
        self.transient(local_login)
        self.grab_set()

    def _clear(self):
        self.unbind("<Return>")
        for child in self.winfo_children():
            child.destroy()

    def _panel(self):
        panel = ttk.Frame(self, padding=28, style="Panel.TFrame")
        panel.grid(row=0, column=0)
        ttk.Label(panel, text="SO", style="BrandMark.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 12)
        )
        ttk.Label(panel, text="Компания", style="AuthTitle.TLabel").grid(
            row=1, column=0, columnspan=2
        )
        return panel

    def _enable_paste(self, entry: ttk.Entry) -> None:
        menu = tk.Menu(
            entry,
            tearoff=False,
            background=COLORS["panel_soft"],
            foreground=COLORS["text"],
            activebackground=COLORS["accent"],
            activeforeground=COLORS["accent_text"],
        )
        menu.add_command(label="Вставить", command=lambda: self._paste_into(entry))
        entry.bind("<Control-v>", lambda _event: self._paste_into(entry))
        entry.bind("<Control-V>", lambda _event: self._paste_into(entry))
        entry.bind("<Shift-Insert>", lambda _event: self._paste_into(entry))
        entry.bind(
            "<Button-3>",
            lambda event: menu.tk_popup(event.x_root, event.y_root),
        )

    def _paste_into(self, entry: ttk.Entry):
        try:
            value = self.clipboard_get().strip()
        except tk.TclError:
            messagebox.showinfo(
                "Буфер обмена", "В буфере обмена нет текста.", parent=self
            )
            return "break"
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.icursor("end")
        return "break"

    def _show_connection(self):
        self._clear()
        panel = self._panel()
        ttk.Label(
            panel,
            text="Подключение к центральному серверу",
            style="Panel.TLabel",
            foreground=COLORS["muted"],
        ).grid(row=2, column=0, columnspan=2, pady=(3, 18))
        ttk.Label(panel, text="Адрес сервера", style="Panel.TLabel").grid(
            row=3, column=0, sticky="w", pady=5
        )
        ttk.Entry(panel, textvariable=self.server_var, width=36).grid(
            row=3, column=1, padx=(12, 0), pady=5
        )
        ttk.Button(
            panel, text="Продолжить", command=self._connect, style="Accent.TButton"
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        ttk.Button(panel, text="Отмена", command=self.destroy).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        self.bind("<Return>", lambda _event: self._connect())

    def _connect(self):
        self.client = CompanyClient(self.server_var.get().strip())
        try:
            status = self.client.status()
        except CompanyApiError as exc:
            messagebox.showerror("Подключение", str(exc), parent=self)
            return
        self._show_form("setup" if not status["initialized"] else "login")

    def _show_form(self, mode):
        self._clear()
        self.mode = mode
        self.password_var.set("")
        self.repeat_var.set("")
        panel = self._panel()
        titles = {
            "setup": "Создание первого администратора",
            "login": "Вход в компанию",
            "register": "Регистрация по приглашению",
        }
        ttk.Label(
            panel,
            text=titles[mode],
            style="Panel.TLabel",
            foreground=COLORS["muted"],
        ).grid(row=2, column=0, columnspan=2, pady=(3, 18))
        row = 3

        def field(label, variable, secret=False):
            nonlocal row
            ttk.Label(panel, text=label, style="Panel.TLabel").grid(
                row=row, column=0, sticky="w", pady=5
            )
            entry = ttk.Entry(
                panel, textvariable=variable, show="*" if secret else "", width=34
            )
            entry.grid(row=row, column=1, padx=(12, 0), pady=5)
            row += 1
            return entry

        if mode in {"setup", "register"}:
            field("ФИО", self.full_name_var)
        if mode == "register":
            ttk.Label(panel, text="Код приглашения", style="Panel.TLabel").grid(
                row=row, column=0, sticky="w", pady=5
            )
            invite_row = ttk.Frame(panel, style="Panel.TFrame")
            invite_row.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=5)
            invite_entry = ttk.Entry(
                invite_row, textvariable=self.invite_var, width=24
            )
            invite_entry.pack(side="left", fill="x", expand=True)
            ttk.Button(
                invite_row,
                text="Вставить",
                command=lambda: self._paste_into(invite_entry),
            ).pack(side="left", padx=(6, 0))
            self._enable_paste(invite_entry)
            row += 1
            field("Телефон", self.phone_var)
        username_entry = field("Логин", self.username_var)
        field("Пароль", self.password_var, True)
        if mode in {"setup", "register"}:
            field("Повтор пароля", self.repeat_var, True)

        ttk.Button(
            panel,
            text="Создать администратора"
            if mode == "setup"
            else ("Зарегистрироваться" if mode == "register" else "Войти"),
            command=self._submit,
            style="Accent.TButton",
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        row += 1
        if mode == "login":
            ttk.Button(
                panel,
                text="Регистрация сотрудника",
                command=lambda: self._show_form("register"),
            ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
            row += 1
        ttk.Button(panel, text="Назад", command=self._show_connection).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        self.bind("<Return>", lambda _event: self._submit())
        username_entry.focus_set()

    def _submit(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        try:
            if self.mode in {"setup", "register"}:
                if password != self.repeat_var.get():
                    raise CompanyApiError("Пароли не совпадают.")
                if self.mode == "setup":
                    self.client.setup_admin(
                        username, password, self.full_name_var.get().strip()
                    )
                else:
                    self.client.register(
                        self.invite_var.get().strip(),
                        username,
                        password,
                        self.full_name_var.get().strip(),
                        self.phone_var.get().strip(),
                    )
                messagebox.showinfo(
                    "Компания", "Учётная запись создана. Выполните вход.", parent=self
                )
                self._show_form("login")
                return
            self.client.login(username, password)
        except CompanyApiError as exc:
            messagebox.showerror("Компания", str(exc), parent=self)
            return

        self.grab_release()
        self.destroy()
        self.local_login.withdraw()
        settings = SettingsService()
        settings.ensure_defaults()
        MainWindow(
            self.local_login,
            crypto=None,
            settings=settings,
            company_client=self.client,
        )

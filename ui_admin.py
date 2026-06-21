import threading
import tkinter as tk
from tkinter import messagebox, ttk
import json

from admin_api_client import AdminApiClient, AdminApiError
from admin_server_control import ComposeServerController, ServerCommandError, local_server_url
from ui_theme import COLORS, apply_theme


class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SecureOffice Admin")
        self.geometry("1100x720")
        self.minsize(980, 620)
        apply_theme(self)

        self.server = ComposeServerController()
        self.server_url_var = tk.StringVar(value="http://127.0.0.1:8765")
        self.lan_url_var = tk.StringVar(value=local_server_url())
        self.status_var = tk.StringVar(value="Сервер не проверен.")
        self.output_var = tk.StringVar(value="")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.repeat_var = tk.StringVar()
        self.display_name_var = tk.StringVar()
        self.employee_name_var = tk.StringVar()
        self.employee_email_var = tk.StringVar()
        self.employee_phone_var = tk.StringVar()
        self.activation_key_var = tk.StringVar(value="")
        self.entry_service_var = tk.StringVar()
        self.entry_url_var = tk.StringVar()
        self.entry_login_var = tk.StringVar()
        self.entry_password_var = tk.StringVar()
        self.entry_comment_var = tk.StringVar()
        self.entry_favorite_var = tk.BooleanVar(value=False)
        self.selected_entry_id: int | None = None
        self.client: AdminApiClient | None = None
        self.employees: list[dict] = []
        self.password_entries: list[dict] = []

        self._build_layout()
        self._check_server()

    def _build_layout(self) -> None:
        shell = ttk.Frame(self)
        shell.pack(fill="both", expand=True)

        sidebar = ttk.Frame(shell, width=260, padding=20, style="Sidebar.TFrame")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="SO", style="BrandMark.TLabel").pack(anchor="w")
        ttk.Label(sidebar, text="SecureOffice", style="Brand.TLabel").pack(
            anchor="w", pady=(16, 4)
        )
        ttk.Label(
            sidebar,
            text="Админское приложение",
            style="SidebarMuted.TLabel",
        ).pack(anchor="w", pady=(0, 22))

        ttk.Button(
            sidebar,
            text="Запустить сервер",
            command=self._start_server,
            style="Accent.TButton",
        ).pack(fill="x", pady=(0, 8))
        ttk.Button(sidebar, text="Проверить статус", command=self._check_server).pack(
            fill="x", pady=(0, 8)
        )
        ttk.Button(sidebar, text="Остановить сервер", command=self._stop_server).pack(
            fill="x", pady=(0, 22)
        )

        ttk.Label(sidebar, text="Локальный адрес", style="SidebarMuted.TLabel").pack(
            anchor="w"
        )
        self._readonly_entry(sidebar, self.server_url_var).pack(fill="x", pady=(4, 12))
        ttk.Label(sidebar, text="Адрес для сети", style="SidebarMuted.TLabel").pack(
            anchor="w"
        )
        self._readonly_entry(sidebar, self.lan_url_var).pack(fill="x", pady=(4, 8))
        ttk.Button(sidebar, text="Скопировать ссылку", command=self._copy_lan_url).pack(
            fill="x"
        )

        self.content = ttk.Frame(shell, padding=24)
        self.content.pack(side="left", fill="both", expand=True)

        self._build_server_panel()
        self.auth_frame = ttk.LabelFrame(self.content, text="Администратор", padding=18)
        self.auth_frame.pack(fill="x", pady=(0, 16))
        self._build_auth_panel("loading")

        self.work_frame = ttk.Frame(self.content)
        self.work_frame.pack(fill="both", expand=True)
        self.tabs = ttk.Notebook(self.work_frame)
        self.tabs.pack(fill="both", expand=True)
        self.employees_tab = ttk.Frame(self.tabs, padding=14)
        self.passwords_tab = ttk.Frame(self.tabs, padding=14)
        self.audit_tab = ttk.Frame(self.tabs, padding=14)
        self.tabs.add(self.employees_tab, text="Сотрудники")
        self.tabs.add(self.passwords_tab, text="Пароли")
        self.tabs.add(self.audit_tab, text="Журнал")
        self._build_employee_panel()
        self._build_password_panel()
        self._build_audit_panel()
        self._set_work_enabled(False)

    def _build_server_panel(self) -> None:
        panel = ttk.Frame(self.content, style="Panel.TFrame", padding=18)
        panel.pack(fill="x", pady=(0, 16))
        ttk.Label(panel, text="Сервер", style="AuthTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(panel, textvariable=self.status_var, style="Panel.TLabel").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(
            panel,
            textvariable=self.output_var,
            style="Panel.TLabel",
            foreground=COLORS["muted"],
            wraplength=720,
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        panel.columnconfigure(0, weight=1)

    def _build_auth_panel(self, mode: str) -> None:
        for child in self.auth_frame.winfo_children():
            child.destroy()
        self.auth_mode = mode
        if mode == "loading":
            ttk.Label(self.auth_frame, text="Проверяю сервер...").pack(anchor="w")
            return

        title = "Создание первого администратора" if mode == "setup" else "Вход администратора"
        ttk.Label(self.auth_frame, text=title, style="Panel.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10)
        )
        row = 1
        if mode == "setup":
            self._labeled_entry(self.auth_frame, row, "Имя", self.display_name_var)
            row += 1
        self._labeled_entry(self.auth_frame, row, "Логин", self.username_var)
        row += 1
        self._labeled_entry(self.auth_frame, row, "Пароль", self.password_var, secret=True)
        row += 1
        if mode == "setup":
            self._labeled_entry(self.auth_frame, row, "Повтор", self.repeat_var, secret=True)
            row += 1
        button_text = "Создать администратора" if mode == "setup" else "Войти"
        ttk.Button(
            self.auth_frame,
            text=button_text,
            style="Accent.TButton",
            command=self._submit_auth,
        ).grid(row=row, column=1, sticky="ew", pady=(12, 0))
        self.auth_frame.columnconfigure(1, weight=1)

    def _build_employee_panel(self) -> None:
        form = ttk.Frame(self.employees_tab)
        form.pack(fill="x", pady=(0, 14))
        self._labeled_entry(form, 0, "ФИО", self.employee_name_var)
        self._labeled_entry(form, 1, "Email", self.employee_email_var)
        self._labeled_entry(form, 2, "Телефон", self.employee_phone_var)
        ttk.Button(
            form,
            text="Добавить сотрудника",
            style="Accent.TButton",
            command=self._create_employee,
        ).grid(row=3, column=1, sticky="ew", pady=(10, 0))
        form.columnconfigure(1, weight=1)

        table_frame = ttk.Frame(self.employees_tab)
        table_frame.pack(fill="both", expand=True)
        columns = ("name", "email", "phone", "status", "key")
        self.employee_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "name": "ФИО",
            "email": "Email",
            "phone": "Телефон",
            "status": "Статус",
            "key": "Последний ключ",
        }
        for column, text in headings.items():
            self.employee_tree.heading(column, text=text)
            self.employee_tree.column(column, width=160 if column != "name" else 240)
        self.employee_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, command=self.employee_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.employee_tree.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(self.employees_tab)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Обновить", command=self._load_employees).pack(
            side="left"
        )
        ttk.Button(
            actions,
            text="Создать ключ",
            style="Accent.TButton",
            command=self._create_activation_key,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Скопировать ключ", command=self._copy_activation_key).pack(
            side="left", padx=(8, 0)
        )
        ttk.Label(actions, textvariable=self.activation_key_var, style="Muted.TLabel").pack(
            side="left", padx=(12, 0)
        )

    def _build_password_panel(self) -> None:
        form = ttk.LabelFrame(self.passwords_tab, text="Запись", padding=14)
        form.pack(fill="x", pady=(0, 14))
        self._labeled_entry(form, 0, "Сервис", self.entry_service_var)
        self._labeled_entry(form, 1, "URL", self.entry_url_var)
        self._labeled_entry(form, 2, "Логин", self.entry_login_var)
        self._labeled_entry(form, 3, "Пароль", self.entry_password_var)
        self._labeled_entry(form, 4, "Комментарий", self.entry_comment_var)
        ttk.Checkbutton(
            form,
            text="Избранное",
            variable=self.entry_favorite_var,
        ).grid(row=5, column=1, sticky="w", pady=(6, 0))

        ttk.Label(form, text="Сотрудники").grid(row=0, column=2, sticky="nw", padx=(20, 8))
        self.employee_listbox = tk.Listbox(
            form,
            selectmode="extended",
            height=7,
            exportselection=False,
            background=COLORS["panel_soft"],
            foreground=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground=COLORS["accent_text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["line"],
        )
        self.employee_listbox.grid(row=0, column=3, rowspan=6, sticky="nsew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        form_actions = ttk.Frame(form)
        form_actions.grid(row=6, column=1, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Button(
            form_actions,
            text="Добавить выбранным",
            style="Accent.TButton",
            command=self._create_password_entries,
        ).pack(side="left")
        ttk.Button(form_actions, text="Сохранить изменения", command=self._save_password_entry).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(form_actions, text="Очистить форму", command=self._clear_password_form).pack(
            side="left", padx=(8, 0)
        )

        table_frame = ttk.Frame(self.passwords_tab)
        table_frame.pack(fill="both", expand=True)
        columns = ("employee", "service", "url", "login", "password", "updated")
        self.password_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "employee": "Сотрудник",
            "service": "Сервис",
            "url": "URL",
            "login": "Логин",
            "password": "Пароль",
            "updated": "Обновлён",
        }
        for column, text in headings.items():
            self.password_tree.heading(column, text=text)
            self.password_tree.column(column, width=150 if column != "password" else 180)
        self.password_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, command=self.password_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.password_tree.configure(yscrollcommand=scrollbar.set)
        self.password_tree.bind("<<TreeviewSelect>>", lambda _event: self._fill_password_form())

        actions = ttk.Frame(self.passwords_tab)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="Обновить", command=self._load_password_entries).pack(side="left")
        ttk.Button(actions, text="История", command=self._show_password_history).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(
            actions,
            text="Удалить",
            style="Danger.TButton",
            command=self._delete_password_entry,
        ).pack(side="left", padx=(8, 0))

    def _build_audit_panel(self) -> None:
        columns = ("time", "actor", "event", "entity", "details")
        self.audit_tree = ttk.Treeview(
            self.audit_tab,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "time": "Время",
            "actor": "Кто",
            "event": "Событие",
            "entity": "Объект",
            "details": "Детали",
        }
        for column, text in headings.items():
            self.audit_tree.heading(column, text=text)
            self.audit_tree.column(column, width=170 if column != "details" else 320)
        self.audit_tree.pack(fill="both", expand=True)
        ttk.Button(self.audit_tab, text="Обновить журнал", command=self._load_audit_events).pack(
            anchor="w", pady=(14, 0)
        )

    def _labeled_entry(
        self,
        parent: tk.Misc,
        row: int,
        label: str,
        variable: tk.StringVar,
        secret: bool = False,
    ) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variable, show="*" if secret else "")
        entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=5)
        return entry

    def _readonly_entry(self, parent: tk.Misc, variable: tk.StringVar) -> ttk.Entry:
        entry = ttk.Entry(parent, textvariable=variable)
        entry.configure(state="readonly")
        return entry

    def _run_background(self, action, on_success=None) -> None:
        def worker():
            try:
                result = action()
            except Exception as exc:
                self.after(0, lambda: self._show_error(exc))
                return
            if on_success:
                self.after(0, lambda: on_success(result))

        threading.Thread(target=worker, daemon=True).start()

    def _start_server(self) -> None:
        self.status_var.set("Запускаю сервер...")
        self._run_background(self.server.start, self._after_server_command)

    def _stop_server(self) -> None:
        if not messagebox.askyesno("Сервер", "Остановить сервер SecureOffice?"):
            return
        self.status_var.set("Останавливаю сервер...")
        self._run_background(self.server.stop, self._after_server_command)

    def _after_server_command(self, output: str) -> None:
        self.output_var.set(_short_output(output))
        self._check_server()

    def _check_server(self) -> None:
        self.client = AdminApiClient(self.server_url_var.get())
        self.status_var.set("Проверяю сервер...")

        def request_status():
            return self.client.status()

        def apply_status(status: dict):
            initialized = bool(status.get("initialized"))
            self.status_var.set(
                "Сервер работает. Администратор создан."
                if initialized
                else "Сервер работает. Нужен первый администратор."
            )
            self._build_auth_panel("login" if initialized else "setup")

        self._run_background(request_status, apply_status)

    def _submit_auth(self) -> None:
        if self.client is None:
            self.client = AdminApiClient(self.server_url_var.get())
        username = self.username_var.get().strip()
        password = self.password_var.get()
        try:
            if self.auth_mode == "setup":
                if password != self.repeat_var.get():
                    raise AdminApiError("Пароли не совпадают.")
                self.client.setup_admin(username, self.display_name_var.get().strip(), password)
                messagebox.showinfo("Администратор", "Администратор создан. Выполните вход.")
                self._build_auth_panel("login")
                return
            self.client.login(username, password)
        except AdminApiError as exc:
            messagebox.showerror("Администратор", str(exc), parent=self)
            return
        self.status_var.set(f"Вход выполнен: {self.client.user.get('display_name')}")
        self._set_work_enabled(True)
        self._load_employees()
        self._load_password_entries()
        self._load_audit_events()

    def _create_employee(self) -> None:
        if not self.client:
            return
        try:
            employee = self.client.create_employee(
                self.employee_name_var.get(),
                self.employee_email_var.get(),
                self.employee_phone_var.get(),
            )
        except AdminApiError as exc:
            messagebox.showerror("Сотрудник", str(exc), parent=self)
            return
        self.employee_name_var.set("")
        self.employee_email_var.set("")
        self.employee_phone_var.set("")
        self.status_var.set(f"Сотрудник добавлен: {employee['full_name']}")
        self._load_employees()

    def _load_employees(self) -> None:
        if not self.client or not self.client.token:
            return
        try:
            self.employees = self.client.employees()
        except AdminApiError as exc:
            messagebox.showerror("Сотрудники", str(exc), parent=self)
            return
        self.employee_tree.delete(*self.employee_tree.get_children())
        self.employee_listbox.delete(0, "end")
        for employee in self.employees:
            self.employee_tree.insert(
                "",
                "end",
                iid=str(employee["id"]),
                values=(
                    employee["full_name"],
                    employee.get("email", ""),
                    employee.get("phone", ""),
                    "Активирован" if employee.get("has_user") else "Ожидает ключ",
                    _key_status(employee),
                ),
            )
            self.employee_listbox.insert("end", f"{employee['full_name']} [#{employee['id']}]")

    def _create_activation_key(self) -> None:
        if not self.client:
            return
        selection = self.employee_tree.selection()
        if not selection:
            messagebox.showinfo("Ключ", "Выберите сотрудника.", parent=self)
            return
        employee_id = int(selection[0])
        try:
            payload = self.client.create_activation_key(employee_id)
        except AdminApiError as exc:
            messagebox.showerror("Ключ", str(exc), parent=self)
            return
        code = payload["code"]
        self.activation_key_var.set(f"Ключ: {code}")
        self._copy_text(code)
        self.status_var.set("Ключ создан и скопирован в буфер.")
        self._load_employees()

    def _selected_employee_ids(self) -> list[int]:
        ids = []
        for index in self.employee_listbox.curselection():
            if index < len(self.employees):
                ids.append(int(self.employees[index]["id"]))
        return ids

    def _password_form_data(self) -> dict:
        return {
            "service_name": self.entry_service_var.get().strip(),
            "site_url": self.entry_url_var.get().strip(),
            "login": self.entry_login_var.get().strip(),
            "password": self.entry_password_var.get(),
            "comment": self.entry_comment_var.get().strip(),
            "is_favorite": self.entry_favorite_var.get(),
        }

    def _create_password_entries(self) -> None:
        if not self.client:
            return
        employee_ids = self._selected_employee_ids()
        data = self._password_form_data()
        try:
            created = self.client.create_password_entries(employee_ids=employee_ids, **data)
        except AdminApiError as exc:
            messagebox.showerror("Пароли", str(exc), parent=self)
            return
        self.status_var.set(f"Создано записей: {len(created)}")
        self._clear_password_form()
        self._load_password_entries()
        self._load_audit_events()

    def _load_password_entries(self) -> None:
        if not self.client or not self.client.token:
            return
        try:
            self.password_entries = self.client.password_entries()
        except AdminApiError as exc:
            messagebox.showerror("Пароли", str(exc), parent=self)
            return
        self.password_tree.delete(*self.password_tree.get_children())
        for entry in self.password_entries:
            self.password_tree.insert(
                "",
                "end",
                iid=str(entry["id"]),
                values=(
                    entry.get("employee_name", ""),
                    entry["service_name"],
                    entry.get("site_url", ""),
                    entry.get("login", ""),
                    entry.get("password", ""),
                    entry.get("updated_at", ""),
                ),
            )

    def _selected_password_entry(self) -> dict | None:
        selection = self.password_tree.selection()
        if not selection:
            return None
        entry_id = int(selection[0])
        return next((entry for entry in self.password_entries if entry["id"] == entry_id), None)

    def _fill_password_form(self) -> None:
        entry = self._selected_password_entry()
        if entry is None:
            return
        self.selected_entry_id = int(entry["id"])
        self.entry_service_var.set(entry.get("service_name", ""))
        self.entry_url_var.set(entry.get("site_url", ""))
        self.entry_login_var.set(entry.get("login", ""))
        self.entry_password_var.set(entry.get("password", ""))
        self.entry_comment_var.set(entry.get("comment", ""))
        self.entry_favorite_var.set(bool(entry.get("is_favorite")))

    def _save_password_entry(self) -> None:
        if not self.client:
            return
        if self.selected_entry_id is None:
            messagebox.showinfo("Пароли", "Выберите запись для изменения.", parent=self)
            return
        try:
            self.client.update_password_entry(self.selected_entry_id, **self._password_form_data())
        except AdminApiError as exc:
            messagebox.showerror("Пароли", str(exc), parent=self)
            return
        self.status_var.set("Запись обновлена.")
        self._load_password_entries()
        self._load_audit_events()

    def _delete_password_entry(self) -> None:
        if not self.client:
            return
        entry = self._selected_password_entry()
        if entry is None:
            messagebox.showinfo("Пароли", "Выберите запись.", parent=self)
            return
        if not messagebox.askyesno("Удаление", f"Удалить запись {entry['service_name']}?"):
            return
        try:
            self.client.delete_password_entry(int(entry["id"]))
        except AdminApiError as exc:
            messagebox.showerror("Пароли", str(exc), parent=self)
            return
        self.status_var.set("Запись удалена.")
        self._clear_password_form()
        self._load_password_entries()
        self._load_audit_events()

    def _show_password_history(self) -> None:
        if not self.client:
            return
        entry = self._selected_password_entry()
        if entry is None:
            messagebox.showinfo("История", "Выберите запись.", parent=self)
            return
        try:
            history = self.client.password_history(int(entry["id"]))
        except AdminApiError as exc:
            messagebox.showerror("История", str(exc), parent=self)
            return
        lines = [
            f"{item.get('created_at', '')} — {item.get('password', '')}"
            for item in history
        ]
        messagebox.showinfo(
            "История паролей",
            "\n".join(lines) if lines else "Истории пока нет.",
            parent=self,
        )

    def _clear_password_form(self) -> None:
        self.selected_entry_id = None
        self.entry_service_var.set("")
        self.entry_url_var.set("")
        self.entry_login_var.set("")
        self.entry_password_var.set("")
        self.entry_comment_var.set("")
        self.entry_favorite_var.set(False)

    def _load_audit_events(self) -> None:
        if not self.client or not self.client.token:
            return
        try:
            events = self.client.audit_events()
        except AdminApiError as exc:
            messagebox.showerror("Журнал", str(exc), parent=self)
            return
        self.audit_tree.delete(*self.audit_tree.get_children())
        for event in events:
            details = event.get("details") or {}
            self.audit_tree.insert(
                "",
                "end",
                iid=str(event["id"]),
                values=(
                    event.get("created_at", ""),
                    event.get("actor_name") or event.get("actor_username") or "Система",
                    event.get("event_type", ""),
                    f"{event.get('entity_type', '')} #{event.get('entity_id') or ''}",
                    json.dumps(details, ensure_ascii=False),
                ),
            )

    def _copy_activation_key(self) -> None:
        value = self.activation_key_var.get().removeprefix("Ключ: ").strip()
        if value:
            self._copy_text(value)
            self.status_var.set("Ключ скопирован.")

    def _copy_lan_url(self) -> None:
        self._copy_text(self.lan_url_var.get())
        self.status_var.set("Ссылка скопирована.")

    def _copy_text(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)

    def _set_work_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for child in self.work_frame.winfo_children():
            self._set_widget_state(child, state)

    def _set_widget_state(self, widget: tk.Misc, state: str) -> None:
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_widget_state(child, state)

    def _show_error(self, exc: Exception) -> None:
        if isinstance(exc, (AdminApiError, ServerCommandError)):
            messagebox.showerror("SecureOffice", str(exc), parent=self)
            self.status_var.set(str(exc))
            return
        messagebox.showerror("SecureOffice", f"Неожиданная ошибка:\n{exc}", parent=self)
        self.status_var.set("Ошибка.")


def _short_output(output: str) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    return "\n".join(lines[-4:])


def _key_status(employee: dict) -> str:
    if employee.get("activation_used_at"):
        return "Использован"
    if employee.get("activation_expires_at"):
        return f"До {employee['activation_expires_at']}"
    return "Нет"

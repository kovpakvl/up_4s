import threading
import tkinter as tk
from tkinter import messagebox, ttk

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
        self.employee_department_var = tk.StringVar(value="Без отдела")
        self.employee_position_var = tk.StringVar(value="Без должности")
        self.department_name_var = tk.StringVar()
        self.position_name_var = tk.StringVar()
        self.position_department_var = tk.StringVar(value="")
        self.activation_key_var = tk.StringVar(value="")
        self.entry_service_var = tk.StringVar()
        self.entry_url_var = tk.StringVar()
        self.entry_login_var = tk.StringVar()
        self.entry_password_var = tk.StringVar()
        self.entry_comment_var = tk.StringVar()
        self.entry_favorite_var = tk.BooleanVar(value=False)
        self.selected_entry_id: int | None = None
        self.client: AdminApiClient | None = None
        self.can_setup_admin = False
        self.auth_tabs: ttk.Notebook | None = None
        self.employees: list[dict] = []
        self.departments: list[dict] = []
        self.department_by_label: dict[str, int | None] = {}
        self.position_by_label: dict[str, int | None] = {}
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
        ttk.Button(sidebar, text="Скопировать вход", command=self._copy_employee_login_url).pack(
            fill="x", pady=(0, 8)
        )
        ttk.Button(sidebar, text="Скопировать активацию", command=self._copy_employee_activate_url).pack(
            fill="x"
        )

        self.content = ttk.Frame(shell, padding=24)
        self.content.pack(side="left", fill="both", expand=True)

        self._build_server_panel()
        self.auth_frame = ttk.Frame(self.content)
        self.auth_frame.pack(fill="both", expand=True)
        self._build_auth_panel("loading")

        self.work_frame = ttk.Frame(self.content)
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
        self.auth_tabs = None
        self.auth_mode = mode

        card = ttk.Frame(self.auth_frame, padding=30, style="Panel.TFrame")
        card.pack(expand=True)
        card.columnconfigure(0, weight=1)
        self._build_auth_header(card)

        if mode == "loading":
            ttk.Label(
                card,
                text="Проверяю сервер...",
                style="AuthMuted.TLabel",
            ).pack(anchor="w", pady=(18, 0))
            return
        if mode == "offline":
            ttk.Label(
                card,
                text="Сервер недоступен. Запустите сервер или проверьте Docker.",
                style="AuthMuted.TLabel",
                wraplength=360,
                justify="left",
            ).pack(anchor="w", pady=(18, 0))
            actions = ttk.Frame(card, style="Panel.TFrame")
            actions.pack(fill="x", pady=(18, 0))
            ttk.Button(
                actions,
                text="Запустить сервер",
                style="Accent.TButton",
                command=self._start_server,
            ).pack(side="left")
            ttk.Button(
                actions,
                text="Проверить снова",
                command=self._check_server,
            ).pack(side="left", padx=(8, 0))
            return

        self._build_auth_tabs(card, mode)

    def _build_auth_header(self, parent: tk.Misc) -> None:
        brand = ttk.Frame(parent, style="Panel.TFrame")
        brand.pack(fill="x")
        ttk.Label(brand, text="SO", style="BrandMark.TLabel").pack(side="left")
        titles = ttk.Frame(brand, style="Panel.TFrame")
        titles.pack(side="left", padx=(12, 0))
        ttk.Label(titles, text="SecureOffice", style="AuthTitle.TLabel").pack(anchor="w")
        ttk.Label(
            titles,
            text="Администратор",
            style="AuthMuted.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _build_auth_tabs(self, parent: tk.Misc, mode: str) -> None:
        self.auth_tabs = ttk.Notebook(parent, style="Auth.TNotebook")
        self.auth_tabs.pack(fill="x", pady=(20, 0))

        login_tab = ttk.Frame(self.auth_tabs, padding=(0, 18, 0, 0), style="Panel.TFrame")
        register_tab = ttk.Frame(self.auth_tabs, padding=(0, 18, 0, 0), style="Panel.TFrame")
        self.auth_tabs.add(login_tab, text="Войти")
        self.auth_tabs.add(register_tab, text="Зарегистрироваться")

        login_entry = self._build_login_tab(login_tab)
        self._build_register_tab(register_tab)
        self.auth_tabs.select(register_tab if mode == "setup" else login_tab)
        self.auth_tabs.bind("<<NotebookTabChanged>>", self._on_auth_tab_changed)
        if mode != "setup":
            login_entry.focus_set()

    def _build_login_tab(self, parent: tk.Misc) -> ttk.Entry:
        ttk.Label(
            parent,
            text="Войдите под аккаунтом администратора.",
            style="AuthMuted.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        username_entry = self._auth_entry(parent, 1, "Логин", self.username_var)
        self._auth_entry(parent, 2, "Пароль", self.password_var, secret=True)
        ttk.Button(
            parent,
            text="Войти",
            style="Accent.TButton",
            command=lambda: self._submit_auth("login"),
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        parent.columnconfigure(1, weight=1)
        return username_entry

    def _build_register_tab(self, parent: tk.Misc) -> None:
        if not self.can_setup_admin:
            ttk.Label(
                parent,
                text=(
                    "Первый администратор уже создан. "
                    "Для работы войдите под существующим аккаунтом."
                ),
                style="AuthMuted.TLabel",
                wraplength=360,
                justify="left",
            ).grid(row=0, column=0, sticky="w", pady=(0, 14))
            ttk.Button(
                parent,
                text="Перейти ко входу",
                command=self._select_login_tab,
            ).grid(row=1, column=0, sticky="ew")
            parent.columnconfigure(0, weight=1)
            return

        ttk.Label(
            parent,
            text="Создайте первый аккаунт, который будет управлять сервером.",
            style="AuthMuted.TLabel",
            wraplength=360,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._auth_entry(parent, 1, "Имя", self.display_name_var)
        self._auth_entry(parent, 2, "Логин", self.username_var)
        self._auth_entry(parent, 3, "Пароль", self.password_var, secret=True)
        self._auth_entry(parent, 4, "Повтор", self.repeat_var, secret=True)
        ttk.Button(
            parent,
            text="Создать аккаунт",
            style="Accent.TButton",
            command=lambda: self._submit_auth("setup"),
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        parent.columnconfigure(1, weight=1)

    def _auth_entry(
        self,
        parent: tk.Misc,
        row: int,
        label: str,
        variable: tk.StringVar,
        secret: bool = False,
    ) -> ttk.Entry:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(
            row=row, column=0, sticky="w", pady=6
        )
        entry = ttk.Entry(parent, textvariable=variable, show="*" if secret else "", width=38)
        entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=6)
        return entry

    def _on_auth_tab_changed(self, _event=None) -> None:
        if not self.auth_tabs:
            return
        selected = self.auth_tabs.select()
        if not selected:
            return
        tab_text = self.auth_tabs.tab(selected, "text")
        self.auth_mode = (
            "setup"
            if tab_text == "Зарегистрироваться" and self.can_setup_admin
            else "login"
        )

    def _select_login_tab(self) -> None:
        if self.auth_tabs:
            self.auth_tabs.select(0)

    def _build_employee_panel(self) -> None:
        structure = ttk.LabelFrame(
            self.employees_tab,
            text="Отделы и должности",
            padding=14,
        )
        structure.pack(fill="x", pady=(0, 14))
        self._labeled_entry(structure, 0, "Отдел", self.department_name_var)
        ttk.Button(
            structure,
            text="Добавить отдел",
            style="Accent.TButton",
            command=self._create_department,
        ).grid(row=0, column=2, sticky="ew", padx=(12, 0), pady=5)
        ttk.Label(structure, text="Для отдела").grid(row=1, column=0, sticky="w", pady=5)
        self.position_department_combo = ttk.Combobox(
            structure,
            textvariable=self.position_department_var,
            state="readonly",
            width=28,
        )
        self.position_department_combo.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=5)
        self._labeled_entry(structure, 2, "Должность", self.position_name_var)
        ttk.Button(
            structure,
            text="Добавить должность",
            command=self._create_position,
        ).grid(row=2, column=2, sticky="ew", padx=(12, 0), pady=5)
        structure.columnconfigure(1, weight=1)

        form = ttk.LabelFrame(self.employees_tab, text="Сотрудник", padding=14)
        form.pack(fill="x", pady=(0, 14))
        self._labeled_entry(form, 0, "ФИО", self.employee_name_var)
        self._labeled_entry(form, 1, "Email", self.employee_email_var)
        self._labeled_entry(form, 2, "Телефон", self.employee_phone_var)
        ttk.Label(form, text="Отдел").grid(row=0, column=2, sticky="w", padx=(20, 8), pady=5)
        self.employee_department_combo = ttk.Combobox(
            form,
            textvariable=self.employee_department_var,
            state="readonly",
            width=24,
        )
        self.employee_department_combo.grid(row=0, column=3, sticky="ew", pady=5)
        self.employee_department_combo.bind("<<ComboboxSelected>>", self._refresh_position_choices)
        ttk.Label(form, text="Должность").grid(row=1, column=2, sticky="w", padx=(20, 8), pady=5)
        self.employee_position_combo = ttk.Combobox(
            form,
            textvariable=self.employee_position_var,
            state="readonly",
            width=24,
        )
        self.employee_position_combo.grid(row=1, column=3, sticky="ew", pady=5)
        ttk.Button(
            form,
            text="Добавить и выдать ключ",
            style="Accent.TButton",
            command=self._create_employee,
        ).grid(row=3, column=1, columnspan=3, sticky="ew", pady=(10, 0))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        table_frame = ttk.Frame(self.employees_tab)
        table_frame.pack(fill="both", expand=True)
        columns = ("name", "department", "position", "email", "phone", "status", "key")
        self.employee_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "name": "ФИО",
            "department": "Отдел",
            "position": "Должность",
            "email": "Email",
            "phone": "Телефон",
            "status": "Статус",
            "key": "Последний ключ",
        }
        for column, text in headings.items():
            self.employee_tree.heading(column, text=text)
            width = 220 if column == "name" else 145
            self.employee_tree.column(column, width=width)
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
            text="Новый ключ",
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
                self.after(0, lambda error=exc: self._show_error(error))
                return
            if on_success:
                self.after(0, lambda value=result: on_success(value))

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
        was_authenticated = bool(self.client and self.client.token)
        token = self.client.token if self.client else None
        user = self.client.user if self.client else None
        self.client = AdminApiClient(self.server_url_var.get())
        self.client.token = token
        self.client.user = user
        self.status_var.set("Проверяю сервер...")
        if not was_authenticated:
            self._show_auth_gate("loading")

        def request_status():
            return self.client.status()

        def apply_status(status: dict):
            initialized = bool(status.get("initialized"))
            self.can_setup_admin = not initialized
            self.status_var.set(
                "Сервер работает. Администратор создан."
                if initialized
                else "Сервер работает. Нужен первый администратор."
            )
            if not was_authenticated:
                self._show_auth_gate("login" if initialized else "setup")

        self._run_background(request_status, apply_status)

    def _submit_auth(self, mode: str | None = None) -> None:
        if self.client is None:
            self.client = AdminApiClient(self.server_url_var.get())
        username = self.username_var.get().strip()
        password = self.password_var.get()
        auth_mode = mode or self.auth_mode
        try:
            if auth_mode == "setup":
                if password != self.repeat_var.get():
                    raise AdminApiError("Пароли не совпадают.")
                self.client.setup_admin(username, self.display_name_var.get().strip(), password)
                self.can_setup_admin = False
                self.status_var.set("Аккаунт администратора создан. Выполните вход.")
                self._show_auth_gate("login")
                self.after(120, self._show_registration_onboarding)
                return
            self.client.login(username, password)
        except AdminApiError as exc:
            messagebox.showerror("Администратор", str(exc), parent=self)
            return
        self.status_var.set(f"Вход выполнен: {self.client.user.get('display_name')}")
        self._show_workspace()
        self._load_departments()
        self._load_employees()
        self._load_password_entries()
        self._load_audit_events()

    def _show_registration_onboarding(self) -> None:
        first_time = self._ask_choice(
            "Первый запуск",
            "Вы здесь впервые?",
            "Да",
            "Нет",
        )
        if first_time is None:
            return
        if first_time:
            self._show_tutorial_intro()
            return
        wants_tutorial = self._ask_choice(
            "Обучение",
            "Желаете пройти обучение?",
            "Да",
            "Нет",
        )
        if wants_tutorial:
            self._show_tutorial_intro()

    def _ask_choice(
        self,
        title: str,
        text: str,
        yes_text: str,
        no_text: str,
    ) -> bool | None:
        result: dict[str, bool | None] = {"value": None}
        dialog = self._dialog(title, 420, 220)
        panel = ttk.Frame(dialog, padding=26, style="Panel.TFrame")
        panel.pack(fill="both", expand=True)

        ttk.Label(panel, text=title, style="AuthTitle.TLabel").pack(anchor="w")
        ttk.Label(
            panel,
            text=text,
            style="AuthMuted.TLabel",
            wraplength=340,
            justify="left",
        ).pack(anchor="w", pady=(12, 22))

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.pack(fill="x")

        def choose(value: bool | None) -> None:
            result["value"] = value
            dialog.destroy()

        ttk.Button(
            actions,
            text=no_text,
            command=lambda: choose(False),
        ).pack(side="right")
        ttk.Button(
            actions,
            text=yes_text,
            style="Accent.TButton",
            command=lambda: choose(True),
        ).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", lambda: choose(None))
        dialog.wait_window()
        return result["value"]

    def _show_tutorial_intro(self) -> None:
        dialog = self._dialog("Короткое обучение", 520, 360)
        panel = ttk.Frame(dialog, padding=26, style="Panel.TFrame")
        panel.pack(fill="both", expand=True)

        ttk.Label(panel, text="Короткое обучение", style="AuthTitle.TLabel").pack(anchor="w")
        ttk.Label(
            panel,
            text="Базовый порядок работы администратора:",
            style="AuthMuted.TLabel",
        ).pack(anchor="w", pady=(10, 14))

        steps = (
            "1. Запустите сервер и скопируйте ссылку для сотрудников.",
            "2. Добавьте сотрудников и создайте для каждого ключ активации.",
            "3. В разделе паролей выберите сотрудников и добавьте нужные записи.",
            "4. В журнале проверяйте входы, изменения и действия с паролями.",
        )
        for step in steps:
            ttk.Label(
                panel,
                text=step,
                style="Panel.TLabel",
                wraplength=440,
                justify="left",
            ).pack(anchor="w", pady=3)

        ttk.Button(
            panel,
            text="Понятно",
            style="Accent.TButton",
            command=dialog.destroy,
        ).pack(fill="x", pady=(22, 0))
        dialog.wait_window()

    def _dialog(self, title: str, width: int, height: int) -> tk.Toplevel:
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.configure(background=COLORS["bg"])
        dialog.resizable(False, False)
        dialog.transient(self)
        self.update_idletasks()
        x = self.winfo_rootx() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - height) // 2, 0)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.grab_set()
        return dialog

    def _create_employee(self) -> None:
        if not self.client:
            return
        department_id = self._selected_department_id(self.employee_department_var.get())
        position_id = self._selected_position_id(self.employee_position_var.get())
        try:
            employee = self.client.create_employee(
                self.employee_name_var.get(),
                self.employee_email_var.get(),
                self.employee_phone_var.get(),
                department_id=department_id,
                position_id=position_id,
            )
            key_payload = self.client.create_activation_key(int(employee["id"]))
        except AdminApiError as exc:
            messagebox.showerror("Сотрудник", str(exc), parent=self)
            return
        self.employee_name_var.set("")
        self.employee_email_var.set("")
        self.employee_phone_var.set("")
        self.employee_department_var.set("Без отдела")
        self.employee_position_var.set("Без должности")
        self._refresh_position_choices()
        self.status_var.set(f"Сотрудник добавлен: {employee['full_name']}")
        self._show_activation_key(key_payload, employee)
        self._load_employees()

    def _load_departments(self) -> None:
        if not self.client or not self.client.token:
            return
        try:
            self.departments = self.client.departments()
        except AdminApiError as exc:
            messagebox.showerror("Отделы", str(exc), parent=self)
            return
        self._refresh_department_choices()

    def _create_department(self) -> None:
        if not self.client:
            return
        try:
            department = self.client.create_department(self.department_name_var.get())
        except AdminApiError as exc:
            messagebox.showerror("Отдел", str(exc), parent=self)
            return
        self.department_name_var.set("")
        self.status_var.set(f"Отдел сохранён: {department['name']}")
        self._load_departments()
        self._load_audit_events()

    def _create_position(self) -> None:
        if not self.client:
            return
        department_id = self._selected_department_id(self.position_department_var.get())
        if department_id is None:
            messagebox.showinfo("Должность", "Выберите отдел.", parent=self)
            return
        try:
            position = self.client.create_position(department_id, self.position_name_var.get())
        except AdminApiError as exc:
            messagebox.showerror("Должность", str(exc), parent=self)
            return
        self.position_name_var.set("")
        self.status_var.set(f"Должность сохранена: {position['name']}")
        self._load_departments()
        self._load_audit_events()

    def _refresh_department_choices(self) -> None:
        labels = ["Без отдела"]
        self.department_by_label = {"Без отдела": None}
        for department in self.departments:
            label = department["name"]
            labels.append(label)
            self.department_by_label[label] = int(department["id"])

        for combo in (self.employee_department_combo, self.position_department_combo):
            combo.configure(values=labels)

        if self.employee_department_var.get() not in labels:
            self.employee_department_var.set("Без отдела")
        if self.position_department_var.get() not in labels:
            self.position_department_var.set(labels[1] if len(labels) > 1 else "Без отдела")
        self._refresh_position_choices()

    def _refresh_position_choices(self, _event=None) -> None:
        department_id = self._selected_department_id(self.employee_department_var.get())
        labels = ["Без должности"]
        self.position_by_label = {"Без должности": None}
        for department in self.departments:
            if department_id and int(department["id"]) != department_id:
                continue
            for position in department.get("positions", []):
                label = f"{position['name']} ({department['name']})"
                labels.append(label)
                self.position_by_label[label] = int(position["id"])
        self.employee_position_combo.configure(values=labels)
        if self.employee_position_var.get() not in labels:
            self.employee_position_var.set("Без должности")

    def _selected_department_id(self, label: str) -> int | None:
        return self.department_by_label.get(label)

    def _selected_position_id(self, label: str) -> int | None:
        return self.position_by_label.get(label)

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
                    employee.get("department_name") or "—",
                    employee.get("position_name") or "—",
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
        employee = next(
            (item for item in self.employees if int(item["id"]) == employee_id),
            {"id": employee_id, "full_name": f"#{employee_id}"},
        )
        self._show_activation_key(payload, employee)
        self._load_employees()

    def _show_activation_key(self, payload: dict, employee: dict) -> None:
        code = payload["code"]
        activation_url = self._employee_activate_url()
        message = (
            f"Сотрудник: {employee.get('full_name', '')}\n"
            f"Ссылка: {activation_url}\n"
            f"Ключ: {code}\n"
            f"Действует до: {payload.get('expires_at', '')}"
        )
        self.activation_key_var.set(f"Ключ: {code}")
        self._copy_text(message)
        self.status_var.set("Ключ и ссылка активации скопированы в буфер.")

        dialog = self._dialog("Ключ сотрудника", 560, 330)
        panel = ttk.Frame(dialog, padding=26, style="Panel.TFrame")
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Ключ сотрудника", style="AuthTitle.TLabel").pack(anchor="w")
        ttk.Label(
            panel,
            text=employee.get("full_name", ""),
            style="AuthMuted.TLabel",
        ).pack(anchor="w", pady=(4, 18))

        body = tk.Text(panel, height=6, wrap="word")
        body.pack(fill="both", expand=True)
        body.insert("1.0", message)
        body.configure(state="disabled")
        body.configure(
            background=COLORS["panel_soft"],
            foreground=COLORS["text"],
            relief="flat",
            padx=10,
            pady=8,
        )

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.pack(fill="x", pady=(18, 0))
        ttk.Button(
            actions,
            text="Скопировать ещё раз",
            command=lambda: self._copy_text(message),
        ).pack(side="left")
        ttk.Button(
            actions,
            text="Готово",
            style="Accent.TButton",
            command=dialog.destroy,
        ).pack(side="right")
        dialog.wait_window()

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
            self.audit_tree.insert(
                "",
                "end",
                iid=str(event["id"]),
                values=(
                    event.get("created_at", ""),
                    event.get("actor_name") or event.get("actor_username") or "Система",
                    _audit_event_label(event),
                    _audit_entity_label(event),
                    _audit_details_text(event),
                ),
            )

    def _copy_activation_key(self) -> None:
        value = self.activation_key_var.get().removeprefix("Ключ: ").strip()
        if value:
            self._copy_text(value)
            self.status_var.set("Ключ скопирован.")

    def _employee_login_url(self) -> str:
        return f"{self.lan_url_var.get().rstrip('/')}/login"

    def _employee_activate_url(self) -> str:
        return f"{self.lan_url_var.get().rstrip('/')}/activate"

    def _copy_employee_login_url(self) -> None:
        self._copy_text(self._employee_login_url())
        self.status_var.set("Ссылка на вход сотрудника скопирована.")

    def _copy_employee_activate_url(self) -> None:
        self._copy_text(self._employee_activate_url())
        self.status_var.set("Ссылка на активацию сотрудника скопирована.")

    def _copy_text(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)

    def _set_work_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for child in self.work_frame.winfo_children():
            self._set_widget_state(child, state)

    def _show_auth_gate(self, mode: str) -> None:
        self._set_work_enabled(False)
        self.work_frame.pack_forget()
        if not self.auth_frame.winfo_ismapped():
            self.auth_frame.pack(fill="both", expand=True)
        self._build_auth_panel(mode)

    def _show_workspace(self) -> None:
        self.auth_frame.pack_forget()
        if not self.work_frame.winfo_ismapped():
            self.work_frame.pack(fill="both", expand=True)
        self._set_work_enabled(True)

    def _set_widget_state(self, widget: tk.Misc, state: str) -> None:
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_widget_state(child, state)

    def _show_error(self, exc: Exception) -> None:
        if isinstance(exc, (AdminApiError, ServerCommandError)):
            self.client = None
            self._show_auth_gate("offline")
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


def _audit_event_label(event: dict) -> str:
    labels = {
        "admin.created": "Создан администратор",
        "auth.login": "Вход в систему",
        "auth.login_failed": "Неудачная попытка входа",
        "department.created": "Добавлен отдел",
        "position.created": "Добавлена должность",
        "employee.created": "Добавлен сотрудник",
        "activation_key.created": "Выдан ключ сотруднику",
        "employee.activated": "Сотрудник активировал аккаунт",
        "password_entry.created": "Добавлена запись пароля",
        "password_entry.updated": "Изменена запись пароля",
        "password_entry.deleted": "Удалена запись пароля",
    }
    event_type = event.get("event_type", "")
    return labels.get(event_type, event_type.replace("_", " ").replace(".", ": "))


def _audit_entity_label(event: dict) -> str:
    labels = {
        "user": "Пользователь",
        "employee": "Сотрудник",
        "department": "Отдел",
        "position": "Должность",
        "password_entry": "Пароль",
    }
    entity_type = event.get("entity_type", "")
    entity_name = labels.get(entity_type, entity_type or "Объект")
    entity_id = event.get("entity_id")
    return f"{entity_name} #{entity_id}" if entity_id else entity_name


def _audit_details_text(event: dict) -> str:
    details = event.get("details") or {}
    if not details:
        return ""
    parts = []
    if "name" in details:
        parts.append(f"Название: {details['name']}")
    if "expires_at" in details:
        parts.append(f"Действует до: {details['expires_at']}")
    if "password_changed" in details:
        parts.append("Пароль изменён" if details["password_changed"] else "Пароль не менялся")
    if details.get("created_by_admin"):
        parts.append("Создано администратором")
    if details.get("updated_by_admin"):
        parts.append("Изменено администратором")
    if details.get("deleted_by_admin"):
        parts.append("Удалено администратором")
    if "department_id" in details and details["department_id"]:
        parts.append(f"Отдел #{details['department_id']}")
    if "position_id" in details and details["position_id"]:
        parts.append(f"Должность #{details['position_id']}")
    if "employee_id" in details and details["employee_id"]:
        parts.append(f"Сотрудник #{details['employee_id']}")
    return "; ".join(parts)

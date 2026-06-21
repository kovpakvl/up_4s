import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional
import webbrowser

from company_client import (
    CompanyAccountService,
    CompanyApiError,
    CompanyClient,
    CompanyEmployeeService,
)
try:
    import pyperclip
except ImportError:  # pragma: no cover - optional convenience
    pyperclip = None

from employee_service import (
    EmployeeService,
    list_departments,
    list_departments_with_counts,
    list_service_types,
)
from password_generator import generate_password
from secureoffice_service import SecureOfficeService
from settings_service import SettingsService
from ui_account_form import AccountForm
from ui_employee_form import EmployeeForm
from ui_theme import COLORS, apply_theme


class MainWindow(tk.Toplevel):
    def __init__(
        self,
        login_window,
        crypto,
        settings: SettingsService,
        company_client: Optional[CompanyClient] = None,
    ):
        super().__init__(login_window)
        self.login_window = login_window
        self.settings = settings
        self.company_client = company_client
        self.is_company_mode = company_client is not None
        self.is_admin = (
            not self.is_company_mode
            or company_client.user.get("access_role") == "admin"
        )
        if company_client:
            self.employee_service = CompanyEmployeeService(company_client)
            self.account_service = CompanyAccountService(company_client)
        else:
            self.employee_service = EmployeeService()
            self.account_service = SecureOfficeService(crypto)
        self._last_activity_ms = 0
        self._active_page = "dashboard"
        self._nav_buttons: dict[str, ttk.Button] = {}

        self.title("SecureOffice - менеджер корпоративных паролей")
        self.geometry("1220x720")
        self.minsize(980, 600)
        self.protocol("WM_DELETE_WINDOW", self._close_app)
        apply_theme(self)
        self.login_window.report_callback_exception = self._report_callback_exception
        self._build_shell()
        self._bind_activity_tracking()
        self.show_dashboard()
        self._schedule_auto_lock()

    def _build_shell(self) -> None:
        shell = ttk.Frame(self)
        shell.pack(fill="both", expand=True)

        sidebar = ttk.Frame(shell, padding=(14, 18), style="Sidebar.TFrame")
        sidebar.pack(side="left", fill="y")
        brand = ttk.Frame(sidebar, style="Sidebar.TFrame")
        brand.pack(fill="x", padx=8, pady=(0, 24))
        ttk.Label(brand, text="SO", style="BrandMark.TLabel").pack(side="left")
        brand_text = ttk.Frame(brand, style="Sidebar.TFrame")
        brand_text.pack(side="left", padx=(10, 0))
        ttk.Label(brand_text, text="SecureOffice", style="Brand.TLabel").pack(anchor="w")
        ttk.Label(
            brand_text, text="Business Vault", style="SidebarMuted.TLabel"
        ).pack(anchor="w")

        pages: list[tuple[str, str, Callable]] = [("dashboard", "Дашборд", self.show_dashboard)]
        if self.is_admin:
            pages.extend(
                [
                    ("employees", "Сотрудники", self.show_employees),
                    ("departments", "Отделы", self.show_departments),
                ]
            )
        pages.extend(
            [
                ("accounts", "Все аккаунты" if self.is_admin else "Мои аккаунты", self.show_accounts),
                ("generator", "Генератор", self.show_generator),
            ]
        )
        if self.is_company_mode and self.is_admin:
            pages.append(("invitations", "Приглашения", self.show_invitations))
        pages.append(("settings", "Настройки", self.show_settings))
        for key, text, command in pages:
            button = ttk.Button(
                sidebar, text=text, command=command, style="Nav.TButton", width=22
            )
            button.pack(fill="x", pady=2)
            self._nav_buttons[key] = button

        self.content = ttk.Frame(shell, padding=22)
        self.content.pack(side="left", fill="both", expand=True)
        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            padding=(12, 6),
            style="Muted.TLabel",
        ).pack(side="bottom", fill="x")

    def _report_callback_exception(self, exc_type, exc_value, traceback) -> None:
        if isinstance(exc_value, CompanyApiError):
            messagebox.showerror("Сервер компании", str(exc_value), parent=self)
            return
        messagebox.showerror(
            "Ошибка",
            f"Операция не выполнена:\n{exc_value}",
            parent=self,
        )

    def _clear_content(self, page: str) -> None:
        self._active_page = page
        for child in self.content.winfo_children():
            child.destroy()
        for key, button in self._nav_buttons.items():
            button.configure(style="NavActive.TButton" if key == page else "Nav.TButton")

    def _page_header(
        self, title: str, subtitle: str = "", action_text: str = "", action=None
    ) -> ttk.Frame:
        header = ttk.Frame(self.content)
        header.pack(fill="x", pady=(0, 18))
        text = ttk.Frame(header)
        text.pack(side="left")
        ttk.Label(text, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(text, text=subtitle, style="Muted.TLabel").pack(anchor="w")
        if action_text and action:
            ttk.Button(
                header, text=action_text, command=action, style="Accent.TButton"
            ).pack(side="right")
        return header

    def _create_tree(
        self,
        parent,
        columns: list[tuple[str, str, int]],
        on_open: Optional[Callable] = None,
    ) -> ttk.Treeview:
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        tree = ttk.Treeview(
            container,
            columns=[item[0] for item in columns],
            show="headings",
            selectmode="browse",
        )
        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        if on_open:
            tree.bind("<Double-1>", lambda _event: on_open())
        return tree

    def _selected_id(self, tree: ttk.Treeview, label: str) -> Optional[int]:
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Выбор", f"Выберите {label} в таблице.", parent=self)
            return None
        return int(selected[0])

    def show_dashboard(self) -> None:
        self._clear_content("dashboard")
        self._page_header(
            "Панель безопасности",
            (
                "Сводная информация по корпоративным доступам"
                if self.is_admin
                else f"Личное хранилище: {self.company_client.user.get('full_name', '')}"
            ),
            "Добавить сотрудника" if self.is_admin else "",
            self._add_employee if self.is_admin else None,
        )
        stats = self.account_service.dashboard_stats()
        cards = ttk.Frame(self.content)
        cards.pack(fill="x", pady=(0, 18))
        if self.is_admin:
            values = [
                ("Сотрудники", stats["employees"]),
                ("Аккаунты", stats["accounts"]),
                ("Финансовые", stats["financial"]),
                ("Слабые пароли", stats["weak_passwords"]),
                ("Не менялись 90 дней", stats["stale_passwords"]),
            ]
        else:
            values = [
                ("Мои аккаунты", stats["accounts"]),
            ]
        for column, (label, value) in enumerate(values):
            card = ttk.Frame(cards, padding=16, style="Panel.TFrame")
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 10))
            ttk.Label(card, text=label, style="Panel.TLabel", foreground=COLORS["muted"]).pack(
                anchor="w"
            )
            ttk.Label(card, text=str(value), style="Stat.TLabel").pack(anchor="w")
            cards.columnconfigure(column, weight=1)

        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(
            toolbar,
            text="Последние аккаунты" if self.is_admin else "Мои последние аккаунты",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")
        ttk.Button(toolbar, text="Добавить аккаунт", command=self._add_account).pack(
            side="right"
        )
        dashboard_columns = [
            ("service", "Сервис", 220),
            ("type", "Тип", 160),
            ("login", "Логин / email", 220),
            ("changed", "Смена пароля", 170),
        ]
        if self.is_admin:
            dashboard_columns[1:1] = [
                ("employee", "Сотрудник", 210),
                ("department", "Отдел", 150),
            ]
        self.dashboard_tree = self._create_tree(
            self.content, dashboard_columns, self._open_dashboard_account
        )
        for account in self.account_service.list_accounts()[:50]:
            values = [
                ("★ " if account["is_favorite"] else "") + account["service_name"],
                account["service_type_name"],
                account["login"] or account["email"],
                account["password_changed_at"] or account["updated_at"],
            ]
            if self.is_admin:
                values[1:1] = [account["employee_name"], account["department_name"]]
            self.dashboard_tree.insert(
                "", "end", iid=str(account["id"]), values=values
            )

    def show_employees(self, initial_department_id: Optional[int] = None) -> None:
        if not self.is_admin:
            self.show_dashboard()
            return
        self._clear_content("employees")
        self._page_header(
            "Сотрудники",
            "Ответственные лица и закреплённые за ними аккаунты",
            "Добавить сотрудника",
            self._add_employee,
        )
        search_var = tk.StringVar()
        departments = self._departments()
        department_ids = {"Все отделы": None, **{d["name"]: d["id"] for d in departments}}
        initial_department_name = next(
            (
                department["name"]
                for department in departments
                if department["id"] == initial_department_id
            ),
            "Все отделы",
        )
        department_var = tk.StringVar(value=initial_department_name)

        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Label(toolbar, text="Поиск").pack(side="left")
        ttk.Entry(toolbar, textvariable=search_var, width=32).pack(
            side="left", padx=(6, 12)
        )
        ttk.Label(toolbar, text="Отдел").pack(side="left")
        department_box = ttk.Combobox(
            toolbar,
            textvariable=department_var,
            values=list(department_ids),
            state="readonly",
            width=20,
        )
        department_box.pack(side="left", padx=(6, 12))
        ttk.Button(toolbar, text="Изменить", command=self._edit_employee).pack(
            side="right", padx=4
        )
        ttk.Button(toolbar, text="Удалить", command=self._delete_employee).pack(
            side="right", padx=4
        )
        ttk.Button(
            toolbar,
            text="Аккаунты сотрудника",
            command=self._show_selected_employee_accounts,
        ).pack(side="right", padx=4)

        self.employee_tree = self._create_tree(
            self.content,
            [
                ("name", "ФИО", 220),
                ("position", "Должность", 150),
                ("role", "Роль", 140),
                ("department", "Отдел", 140),
                ("phone", "Телефон", 130),
                ("email", "Email", 190),
                ("status", "Статус", 110),
                ("accounts", "Аккаунты", 80),
            ],
            self._edit_employee,
        )

        def refresh(*_args) -> None:
            for item in self.employee_tree.get_children():
                self.employee_tree.delete(item)
            rows = self.employee_service.list_employees(
                search_var.get(), department_ids.get(department_var.get())
            )
            for employee in rows:
                self.employee_tree.insert(
                    "",
                    "end",
                    iid=str(employee["id"]),
                    values=(
                        employee["full_name"],
                        employee["position"],
                        employee["role"],
                        employee["department_name"],
                        employee["phone"],
                        employee["email"],
                        employee["status"],
                        employee["account_count"],
                    ),
                )
            self.status_var.set(f"Сотрудников: {len(rows)}")

        self._refresh_employees = refresh
        search_var.trace_add("write", refresh)
        department_box.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def show_departments(self) -> None:
        if not self.is_admin:
            self.show_dashboard()
            return
        self._clear_content("departments")
        self._page_header("Отделы", "Структура компании и количество сотрудников")
        self.department_tree = self._create_tree(
            self.content,
            [
                ("name", "Название отдела", 320),
                ("employees", "Количество сотрудников", 180),
            ],
            self._open_department,
        )
        for department in self._departments_with_counts():
            self.department_tree.insert(
                "",
                "end",
                iid=str(department["id"]),
                values=(department["name"], department["employee_count"]),
            )
        ttk.Label(
            self.content,
            text="Дважды щёлкните отдел, чтобы открыть список его сотрудников.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    def show_accounts(
        self, employee_id: Optional[int] = None, department_id: Optional[int] = None
    ) -> None:
        self._clear_content("accounts")
        self._page_header(
            "Корпоративные аккаунты",
            "Зашифрованные логины и пароли сервисов",
            "Добавить аккаунт",
            lambda: self._add_account(employee_id),
        )
        search_var = tk.StringVar()
        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Label(toolbar, text="Поиск").pack(side="left")
        ttk.Entry(toolbar, textvariable=search_var, width=38).pack(
            side="left", padx=(6, 12)
        )
        ttk.Button(toolbar, text="Открыть", command=self._open_account).pack(
            side="right", padx=4
        )
        ttk.Button(toolbar, text="Изменить", command=self._edit_account).pack(
            side="right", padx=4
        )
        ttk.Button(toolbar, text="Удалить", command=self._delete_account).pack(
            side="right", padx=4
        )

        self.account_tree = self._create_tree(
            self.content,
            [
                ("service", "Сервис", 180),
                ("employee", "Сотрудник", 200),
                ("department", "Отдел", 140),
                ("type", "Тип", 140),
                ("login", "Логин / email", 180),
                ("changed", "Смена пароля", 150),
            ],
            self._open_account,
        )

        def refresh(*_args) -> None:
            for item in self.account_tree.get_children():
                self.account_tree.delete(item)
            rows = self.account_service.list_accounts(
                employee_id, search_var.get(), department_id
            )
            for account in rows:
                self.account_tree.insert(
                    "",
                    "end",
                    iid=str(account["id"]),
                    values=(
                        ("★ " if account["is_favorite"] else "") + account["service_name"],
                        account["employee_name"],
                        account["department_name"],
                        account["service_type_name"],
                        account["login"] or account["email"],
                        account["password_changed_at"] or account["updated_at"],
                    ),
                )
            self.status_var.set(f"Аккаунтов: {len(rows)}")

        self._refresh_accounts = refresh
        search_var.trace_add("write", refresh)
        refresh()

    def show_generator(self) -> None:
        self._clear_content("generator")
        self._page_header("Генератор паролей", "Создание криптографически стойких паролей")
        panel = ttk.LabelFrame(self.content, text="Параметры", padding=18)
        panel.pack(fill="x")
        length_var = tk.IntVar(value=self._default_password_length())
        digits_var = tk.BooleanVar(value=True)
        lowercase_var = tk.BooleanVar(value=True)
        uppercase_var = tk.BooleanVar(value=True)
        special_var = tk.BooleanVar(value=True)
        similar_var = tk.BooleanVar(value=False)
        result_var = tk.StringVar()

        ttk.Label(panel, text="Длина").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Spinbox(panel, from_=4, to=128, textvariable=length_var, width=10).grid(
            row=0, column=1, sticky="w", pady=5
        )
        options = [
            ("Цифры", digits_var),
            ("Строчные буквы", lowercase_var),
            ("Заглавные буквы", uppercase_var),
            ("Спецсимволы", special_var),
            ("Исключить похожие символы", similar_var),
        ]
        for row, (text, variable) in enumerate(options, start=1):
            ttk.Checkbutton(
                panel, text=text, variable=variable, style="Panel.TCheckbutton"
            ).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=3
            )

        def create_password() -> None:
            try:
                result_var.set(
                    generate_password(
                        length=length_var.get(),
                        use_digits=digits_var.get(),
                        use_lowercase=lowercase_var.get(),
                        use_uppercase=uppercase_var.get(),
                        use_special=special_var.get(),
                        exclude_similar=similar_var.get(),
                    )
                )
            except (ValueError, tk.TclError) as exc:
                messagebox.showerror("Генератор", str(exc), parent=self)

        ttk.Button(
            panel,
            text="Сгенерировать",
            command=create_password,
            style="Accent.TButton",
        ).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        result = ttk.LabelFrame(self.content, text="Результат", padding=18)
        result.pack(fill="x", pady=(16, 0))
        ttk.Entry(result, textvariable=result_var, font=("Consolas", 12)).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            result,
            text="Копировать",
            command=lambda: self._copy(result_var.get(), "Пароль"),
            style="Accent.TButton",
        ).pack(side="left", padx=(8, 0))

    def show_settings(self) -> None:
        self._clear_content("settings")
        self._page_header("Настройки", "Параметры безопасности настольного приложения")
        values = self.settings.all()
        panel = ttk.LabelFrame(self.content, text="Безопасность", padding=18)
        panel.pack(fill="x")
        clipboard_var = tk.StringVar(value=values["clipboard_clear_seconds"])
        lock_var = tk.StringVar(value=values["auto_lock_minutes"])
        length_var = tk.StringVar(value=values["default_password_length"])
        fields = [
            ("Очистка буфера обмена, сек.", clipboard_var),
            ("Автоблокировка, мин.", lock_var),
            ("Длина пароля по умолчанию", length_var),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(panel, textvariable=variable, width=16).grid(
                row=row, column=1, sticky="w", padx=(12, 0), pady=6
            )

        def save() -> None:
            try:
                clipboard = max(0, int(clipboard_var.get()))
                lock = max(0, int(lock_var.get()))
                length = min(128, max(4, int(length_var.get())))
            except ValueError:
                messagebox.showerror(
                    "Настройки", "Введите целые числовые значения.", parent=self
                )
                return
            self.settings.set("clipboard_clear_seconds", str(clipboard))
            self.settings.set("auto_lock_minutes", str(lock))
            self.settings.set("default_password_length", str(length))
            self.status_var.set("Настройки сохранены.")

        actions = ttk.Frame(self.content)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(
            actions, text="Сохранить", command=save, style="Accent.TButton"
        ).pack(side="left")
        if not self.is_company_mode:
            ttk.Button(
                actions, text="Создать резервную копию", command=self._backup
            ).pack(side="left", padx=(8, 0))
        else:
            if self.is_admin:
                ttk.Button(
                    actions,
                    text="Резервная копия сервера",
                    command=self._company_backup,
                ).pack(side="left", padx=(8, 0))
            ttk.Label(
                self.content,
                text=(
                    "Резервная копия создаётся на центральном сервере."
                    if self.is_admin
                    else "Резервным копированием управляет администратор."
                ),
                style="Muted.TLabel",
            ).pack(anchor="w", pady=(12, 0))

    def show_invitations(self) -> None:
        if not self.is_company_mode or not self.is_admin:
            self.show_dashboard()
            return
        self._clear_content("invitations")
        self._page_header(
            "Приглашения",
            "Создайте одноразовый код для регистрации сотрудника",
        )
        departments = self._departments()
        department_by_name = {item["name"]: item["id"] for item in departments}
        department_var = tk.StringVar(
            value=departments[0]["name"] if departments else ""
        )
        email_var = tk.StringVar()
        role_var = tk.StringVar(value="Сотрудник")
        panel = ttk.LabelFrame(self.content, text="Новое приглашение", padding=18)
        panel.pack(fill="x")
        fields = [
            ("Email сотрудника", ttk.Entry(panel, textvariable=email_var, width=36)),
            (
                "Отдел",
                ttk.Combobox(
                    panel,
                    textvariable=department_var,
                    values=list(department_by_name),
                    state="readonly",
                    width=33,
                ),
            ),
            (
                "Роль",
                ttk.Combobox(
                    panel,
                    textvariable=role_var,
                    values=(
                        "Администратор",
                        "Бухгалтер",
                        "Менеджер",
                        "Маркетолог",
                        "Директор",
                        "Сотрудник",
                    ),
                    state="readonly",
                    width=33,
                ),
            ),
        ]
        for row, (label, widget) in enumerate(fields):
            ttk.Label(panel, text=label, style="Panel.TLabel").grid(
                row=row, column=0, sticky="w", pady=6
            )
            widget.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=6)
        result_var = tk.StringVar()
        ttk.Label(panel, textvariable=result_var, style="Panel.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        def create():
            department_id = department_by_name.get(department_var.get())
            if not department_id:
                messagebox.showerror("Приглашение", "Выберите отдел.", parent=self)
                return
            try:
                payload = self.company_client.create_invitation(
                    email_var.get().strip(), department_id, role_var.get()
                )
            except CompanyApiError as exc:
                messagebox.showerror("Приглашение", str(exc), parent=self)
                return
            code = payload["code"]
            result_var.set(f"Код: {code}\nДействует до: {payload['expires_at']}")
            self._copy(code, "Код приглашения")

        ttk.Button(
            panel,
            text="Создать и скопировать код",
            command=create,
            style="Accent.TButton",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _add_employee(self, navigate: bool = True) -> Optional[int]:
        form = EmployeeForm(self, self._departments())
        self.wait_window(form)
        if form.result:
            employee_id = self.employee_service.add_employee(form.result)
            self.status_var.set("Сотрудник добавлен.")
            if navigate:
                self.show_employees()
            return employee_id
        return None

    def _edit_employee(self) -> None:
        employee_id = self._selected_id(self.employee_tree, "сотрудника")
        if employee_id is None:
            return
        employee = self.employee_service.get_employee(employee_id)
        if employee is None:
            messagebox.showerror("Сотрудник", "Сотрудник не найден.", parent=self)
            return
        form = EmployeeForm(self, self._departments(), employee)
        self.wait_window(form)
        if form.result:
            self.employee_service.update_employee(form.result)
            self.status_var.set("Данные сотрудника обновлены.")
            self.show_employees()

    def _delete_employee(self) -> None:
        employee_id = self._selected_id(self.employee_tree, "сотрудника")
        if employee_id is None:
            return
        employee = self.employee_service.get_employee(employee_id)
        if employee and messagebox.askyesno(
            "Удаление", f"Удалить сотрудника {employee['full_name']}?", parent=self
        ):
            if self.employee_service.delete_employee(employee_id):
                self.status_var.set("Сотрудник удалён.")
                self.show_employees()
            else:
                messagebox.showerror(
                    "Удаление",
                    "Нельзя удалить сотрудника, пока за ним закреплены аккаунты.",
                    parent=self,
                )

    def _show_selected_employee_accounts(self) -> None:
        employee_id = self._selected_id(self.employee_tree, "сотрудника")
        if employee_id is not None:
            self.show_accounts(employee_id=employee_id)

    def _open_department(self) -> None:
        department_id = self._selected_id(self.department_tree, "отдел")
        if department_id is not None:
            self.show_employees(initial_department_id=department_id)

    def _department_name(self, department_id: int) -> str:
        return next(
            (item["name"] for item in self._departments() if item["id"] == department_id),
            "",
        )

    def _add_account(self, selected_employee_id: Optional[int] = None) -> None:
        employees = self.employee_service.list_employees()
        if not employees:
            messagebox.showinfo(
                "Аккаунт", "Сначала добавьте хотя бы одного сотрудника.", parent=self
            )
            selected_employee_id = self._add_employee(navigate=False)
            if selected_employee_id is None:
                return
            employees = self.employee_service.list_employees()
        form = AccountForm(
            self,
            employees,
            self._departments(),
            self._service_types(),
            selected_employee_id=selected_employee_id,
            default_length=self._default_password_length(),
        )
        self.wait_window(form)
        if form.result:
            self.account_service.add_account(form.result)
            self.status_var.set("Аккаунт добавлен.")
            self.show_accounts()

    def _open_dashboard_account(self) -> None:
        account_id = self._selected_id(self.dashboard_tree, "аккаунт")
        if account_id is not None:
            self._show_account_dialog(account_id)

    def _open_account(self) -> None:
        account_id = self._selected_id(self.account_tree, "аккаунт")
        if account_id is not None:
            self._show_account_dialog(account_id)

    def _show_account_dialog(self, account_id: int) -> None:
        account = self.account_service.get_account(account_id)
        if account is None:
            messagebox.showerror("Аккаунт", "Аккаунт не найден.", parent=self)
            return
        window = tk.Toplevel(self)
        window.title(account["service_name"])
        window.resizable(False, False)
        apply_theme(window)
        window.transient(self)
        frame = ttk.Frame(window, padding=18, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)
        rows = [
            ("Сервис", account["service_name"]),
            ("Сотрудник", account["employee_name"]),
            ("Отдел", account["department_name"]),
            ("Тип", account["service_type_name"]),
            ("Сайт", account["site_url"] or "Не указан"),
            ("Логин", account["login"] or "Не указан"),
            ("Email", account["email"] or "Не указан"),
            ("Смена пароля", account["password_changed_at"]),
            ("Комментарий", account["comment"] or "Нет комментария"),
        ]
        for row, (label, value) in enumerate(rows):
            ttk.Label(
                frame,
                text=label,
                font=("Segoe UI", 9, "bold"),
                style="Panel.TLabel",
            ).grid(
                row=row, column=0, sticky="nw", pady=4
            )
            ttk.Label(frame, text=value, wraplength=430, style="Panel.TLabel").grid(
                row=row, column=1, sticky="w", padx=(14, 0), pady=4
            )
        ttk.Label(
            frame,
            text="Пароль",
            font=("Segoe UI", 9, "bold"),
            style="Panel.TLabel",
        ).grid(
            row=9, column=0, sticky="w", pady=4
        )
        password_var = tk.StringVar(value="••••••••••••")
        ttk.Label(
            frame,
            textvariable=password_var,
            font=("Consolas", 10),
            style="Panel.TLabel",
        ).grid(
            row=9, column=1, sticky="w", padx=(14, 0), pady=4
        )
        status = "Слабый пароль" if account["is_weak"] else "Пароль выглядит надёжным"
        ttk.Label(
            frame,
            text=status,
            style="Panel.TLabel",
            foreground=COLORS["warning"] if account["is_weak"] else COLORS["accent"],
        ).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.grid(row=11, column=0, columnspan=2, sticky="e", pady=(16, 0))

        def reveal() -> None:
            password_var.set(account["password"])
            window.after(10_000, lambda: password_var.set("••••••••••••"))

        ttk.Button(buttons, text="Показать на 10 сек.", command=reveal).pack(
            side="left", padx=4
        )
        ttk.Button(
            buttons,
            text="Копировать логин",
            command=lambda: self._copy(
                account["login"] or account["email"], "Логин"
            ),
        ).pack(side="left", padx=4)
        ttk.Button(
            buttons,
            text="Копировать пароль",
            command=lambda: self._copy(account["password"], "Пароль"),
        ).pack(side="left", padx=4)
        if account["site_url"]:
            ttk.Button(
                buttons,
                text="Открыть сайт",
                command=lambda: webbrowser.open(account["site_url"]),
            ).pack(side="left", padx=4)
        ttk.Button(buttons, text="Закрыть", command=window.destroy).pack(
            side="left", padx=4
        )

    def _edit_account(self) -> None:
        account_id = self._selected_id(self.account_tree, "аккаунт")
        if account_id is None:
            return
        account = self.account_service.get_account(account_id)
        if account is None:
            messagebox.showerror("Аккаунт", "Аккаунт не найден.", parent=self)
            return
        form = AccountForm(
            self,
            self.employee_service.list_employees(),
            self._departments(),
            self._service_types(),
            account=account,
            default_length=self._default_password_length(),
        )
        self.wait_window(form)
        if form.result:
            self.account_service.update_account(form.result, form.password_changed)
            self.status_var.set("Аккаунт обновлён.")
            self.show_accounts()

    def _delete_account(self) -> None:
        account_id = self._selected_id(self.account_tree, "аккаунт")
        if account_id is None:
            return
        account = self.account_service.get_account(account_id)
        if account and messagebox.askyesno(
            "Удаление", f"Удалить аккаунт {account['service_name']}?", parent=self
        ):
            self.account_service.delete_account(account_id)
            self.status_var.set("Аккаунт удалён.")
            self.show_accounts()

    def _backup(self) -> None:
        try:
            path = self.settings.create_backup()
        except OSError as exc:
            messagebox.showerror("Резервная копия", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Резервная копия", f"Создан файл:\n{path}", parent=self
        )

    def _company_backup(self) -> None:
        try:
            payload = self.company_client.create_backup()
        except CompanyApiError as exc:
            messagebox.showerror("Резервная копия", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Резервная копия",
            "На сервере созданы файлы:\n"
            f"{payload['database']}\n{payload['key']}",
            parent=self,
        )

    def _copy(self, value: str, label: str) -> None:
        if not value:
            messagebox.showinfo("Буфер обмена", "Нет значения для копирования.", parent=self)
            return
        if pyperclip:
            pyperclip.copy(value)
        else:
            self.clipboard_clear()
            self.clipboard_append(value)
        self.status_var.set(f"{label} скопирован.")
        seconds = self._setting_int("clipboard_clear_seconds", 30)
        if seconds > 0:
            self.after(seconds * 1000, self._clear_clipboard)

    def _clear_clipboard(self) -> None:
        try:
            if pyperclip:
                pyperclip.copy("")
            else:
                self.clipboard_clear()
            self.status_var.set("Буфер обмена очищен.")
        except tk.TclError:
            pass

    def _default_password_length(self) -> int:
        return min(128, max(4, self._setting_int("default_password_length", 16)))

    def _setting_int(self, name: str, default: int) -> int:
        try:
            return int(self.settings.get(name, str(default)) or default)
        except ValueError:
            return default

    def _departments(self) -> list[dict]:
        return (
            self.company_client.departments()
            if self.company_client
            else list_departments()
        )

    def _departments_with_counts(self) -> list[dict]:
        return (
            self.company_client.departments()
            if self.company_client
            else list_departments_with_counts()
        )

    def _service_types(self) -> list[dict]:
        return (
            self.company_client.service_types()
            if self.company_client
            else list_service_types()
        )

    def _bind_activity_tracking(self) -> None:
        self._touch_activity()
        for event in ("<Button>", "<Key>", "<Motion>"):
            self.bind_all(event, self._touch_activity, add="+")

    def _touch_activity(self, _event=None) -> None:
        self._last_activity_ms = int(self.tk.call("clock", "milliseconds"))

    def _schedule_auto_lock(self) -> None:
        self.after(30_000, self._check_auto_lock)

    def _check_auto_lock(self) -> None:
        minutes = self._setting_int("auto_lock_minutes", 5)
        now_ms = int(self.tk.call("clock", "milliseconds"))
        if minutes > 0 and now_ms - self._last_activity_ms >= minutes * 60_000:
            self._lock()
            return
        self.after(30_000, self._check_auto_lock)

    def _lock(self) -> None:
        if self.company_client:
            try:
                self.company_client.logout()
            except CompanyApiError:
                pass
        self.destroy()
        self.login_window.show_again()

    def _close_app(self) -> None:
        if self.company_client:
            try:
                self.company_client.logout()
            except CompanyApiError:
                pass
        self.login_window.destroy()

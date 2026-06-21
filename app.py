import os
import uuid
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import auth
from config import EMPLOYEE_ROLES, EMPLOYEE_STATUSES, PROJECT_NAME
from crypto_service import CryptoService
from database import ensure_database, has_user, reset_vault
from employee_service import (
    Employee,
    EmployeeService,
    get_department,
    list_departments,
    list_departments_with_counts,
    list_service_types,
)
from password_generator import generate_password
from secureoffice_service import BusinessAccount, SecureOfficeService
from settings_service import SettingsService


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECUREOFFICE_SECRET_KEY", "secureoffice-local-dev-secret"
)
app.config["PROJECT_NAME"] = PROJECT_NAME

_VAULT_SESSIONS = {}


def get_crypto():
    token = session.get("vault_token")
    return _VAULT_SESSIONS.get(token)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if get_crypto() is None:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


@app.before_request
def prepare_database():
    ensure_database()
    SettingsService().ensure_defaults()


@app.context_processor
def inject_globals():
    return {"project_name": PROJECT_NAME}


@app.route("/")
def index():
    if not has_user():
        return redirect(url_for("setup"))
    if get_crypto() is None:
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if has_user():
        return redirect(url_for("login"))
    if request.method == "POST":
        password = request.form.get("password", "")
        repeat_password = request.form.get("repeat_password", "")
        ok, error = auth.validate_new_master_password(password, repeat_password)
        if not ok:
            flash(error, "danger")
            return render_template("setup.html")
        salt = auth.create_user(password)
        token = str(uuid.uuid4())
        _VAULT_SESSIONS[token] = CryptoService(password, salt)
        session["vault_token"] = token
        flash("Мастер-пароль создан. SecureOffice готов к работе.", "success")
        return redirect(url_for("dashboard"))
    return render_template("setup.html")


@app.route("/reset-vault", methods=["GET", "POST"])
def reset_vault_route():
    if request.method == "POST":
        if request.form.get("confirm") != "RESET":
            flash("Введите RESET для подтверждения создания нового хранилища.", "danger")
            return render_template("reset_vault.html")
        token = session.pop("vault_token", None)
        if token:
            _VAULT_SESSIONS.pop(token, None)
        reset_vault()
        flash("Старое хранилище очищено. Теперь создайте новый мастер-пароль.", "success")
        return redirect(url_for("setup"))
    return render_template("reset_vault.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if not has_user():
        return redirect(url_for("setup"))
    if request.method == "POST":
        password = request.form.get("password", "")
        salt = auth.verify_master_password(password)
        if salt is None:
            flash("Неверный мастер-пароль.", "danger")
            return render_template("login.html")
        token = str(uuid.uuid4())
        _VAULT_SESSIONS[token] = CryptoService(password, salt)
        session["vault_token"] = token
        flash("Вход выполнен.", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    token = session.pop("vault_token", None)
    if token:
        _VAULT_SESSIONS.pop(token, None)
    flash("Хранилище заблокировано.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    employee_service = EmployeeService()
    account_service = SecureOfficeService(get_crypto())
    selected_department_id = request.args.get("department_id", type=int)
    employees = employee_service.list_employees(
        request.args.get("employee_search", ""), selected_department_id
    )
    selected_employee_id = request.args.get("employee_id", type=int)
    employee_ids = {employee["id"] for employee in employees}
    if selected_employee_id not in employee_ids:
        selected_employee_id = employees[0]["id"] if employees else None
    selected_employee = (
        employee_service.get_employee(selected_employee_id)
        if selected_employee_id
        else None
    )
    accounts = account_service.list_accounts(
        selected_employee_id, request.args.get("account_search", "")
    )
    return render_template(
        "dashboard.html",
        stats=account_service.dashboard_stats(),
        employees=employees,
        selected_employee=selected_employee,
        selected_employee_id=selected_employee_id,
        selected_department_id=selected_department_id,
        selected_department=get_department(selected_department_id)
        if selected_department_id
        else None,
        departments=list_departments_with_counts(),
        accounts=accounts,
        account_search=request.args.get("account_search", ""),
        employee_search=request.args.get("employee_search", ""),
    )


@app.route("/employees")
@login_required
def employees():
    employee_service = EmployeeService()
    selected_department_id = request.args.get("department_id", type=int)
    return render_template(
        "employees.html",
        employees=employee_service.list_employees(
            request.args.get("q", ""), selected_department_id
        ),
        departments=list_departments_with_counts(),
        selected_department_id=selected_department_id,
        selected_department=get_department(selected_department_id)
        if selected_department_id
        else None,
        query=request.args.get("q", ""),
    )


@app.route("/departments")
@login_required
def departments():
    all_departments = list_departments_with_counts()
    selected_department_id = request.args.get("department_id", type=int)
    if selected_department_id is None and all_departments:
        selected_department_id = all_departments[0]["id"]
    return render_template(
        "departments.html",
        departments=all_departments,
        selected_department_id=selected_department_id,
        selected_department=get_department(selected_department_id)
        if selected_department_id
        else None,
        employees=EmployeeService().list_employees("", selected_department_id),
    )


@app.route("/employees/add", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        employee = _employee_from_form()
        if not employee.full_name:
            flash("ФИО сотрудника обязательно.", "danger")
        else:
            employee_id = EmployeeService().add_employee(employee)
            flash("Сотрудник добавлен.", "success")
            return redirect(url_for("dashboard", employee_id=employee_id))
    return render_template(
        "employee_form.html",
        employee=None,
        departments=list_departments(),
        roles=EMPLOYEE_ROLES,
        statuses=EMPLOYEE_STATUSES,
    )


@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    employee_service = EmployeeService()
    employee = employee_service.get_employee(employee_id)
    if employee is None:
        flash("Сотрудник не найден.", "danger")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        updated = _employee_from_form(employee_id)
        if not updated.full_name:
            flash("ФИО сотрудника обязательно.", "danger")
        else:
            employee_service.update_employee(updated)
            flash("Данные сотрудника обновлены.", "success")
            return redirect(url_for("dashboard", employee_id=employee_id))
    return render_template(
        "employee_form.html",
        employee=employee,
        departments=list_departments(),
        roles=EMPLOYEE_ROLES,
        statuses=EMPLOYEE_STATUSES,
    )


@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id):
    deleted = EmployeeService().delete_employee(employee_id)
    if deleted:
        flash("Сотрудник удален.", "success")
    else:
        flash("Нельзя удалить сотрудника, пока за ним закреплены аккаунты.", "danger")
    return redirect(url_for("dashboard"))


@app.route("/accounts")
@login_required
def accounts():
    account_service = SecureOfficeService(get_crypto())
    return render_template(
        "accounts.html",
        accounts=account_service.list_accounts(query=request.args.get("q", "")),
        query=request.args.get("q", ""),
    )


@app.route("/accounts/add", methods=["GET", "POST"])
@login_required
def add_account():
    selected_employee_id = request.args.get("employee_id", type=int)
    if request.method == "POST":
        account = _account_from_form()
        error = _validate_account(account)
        if error:
            flash(error, "danger")
        else:
            account_id = SecureOfficeService(get_crypto()).add_account(account)
            flash("Аккаунт добавлен.", "success")
            return redirect(url_for("view_account", account_id=account_id))
    return render_account_form(selected_employee_id=selected_employee_id)


@app.route("/accounts/<int:account_id>")
@login_required
def view_account(account_id):
    account = SecureOfficeService(get_crypto()).get_account(account_id)
    if account is None:
        flash("Аккаунт не найден.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("account_detail.html", account=account)


@app.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def edit_account(account_id):
    account_service = SecureOfficeService(get_crypto())
    account = account_service.get_account(account_id)
    if account is None:
        flash("Аккаунт не найден.", "danger")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        updated = _account_from_form(account_id)
        error = _validate_account(updated)
        if error:
            flash(error, "danger")
        else:
            password_changed = updated.password != account["password"]
            account_service.update_account(updated, password_changed)
            flash("Аккаунт обновлен.", "success")
            return redirect(url_for("view_account", account_id=account_id))
    return render_account_form(account=account)


@app.route("/accounts/<int:account_id>/delete", methods=["POST"])
@login_required
def delete_account(account_id):
    SecureOfficeService(get_crypto()).delete_account(account_id)
    flash("Аккаунт удален.", "success")
    return redirect(url_for("dashboard"))


@app.route("/generator", methods=["GET", "POST"])
@login_required
def generator():
    password = ""
    length = int(request.form.get("length", request.args.get("length", 16)) or 16)
    if request.method == "POST":
        try:
            password = generate_password(
                length=length,
                use_digits=bool(request.form.get("digits")),
                use_lowercase=bool(request.form.get("lowercase")),
                use_uppercase=bool(request.form.get("uppercase")),
                use_special=bool(request.form.get("special")),
                exclude_similar=bool(request.form.get("exclude_similar")),
            )
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("generator.html", password=password, length=length)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    service = SettingsService()
    if request.method == "POST":
        if request.form.get("action") == "backup":
            path = service.create_backup()
            flash(f"Резервная копия создана: {path}", "success")
        else:
            service.set("clipboard_clear_seconds", request.form.get("clipboard_clear_seconds", "30"))
            service.set("auto_lock_minutes", request.form.get("auto_lock_minutes", "5"))
            service.set("default_password_length", request.form.get("default_password_length", "16"))
            service.set("theme", request.form.get("theme", "dark"))
            flash("Настройки сохранены.", "success")
    return render_template("settings.html", values=service.all())


def render_account_form(selected_employee_id=None, account=None):
    employees = EmployeeService().list_employees()
    departments = list_departments()
    service_types = list_service_types()
    return render_template(
        "account_form.html",
        account=account,
        employees=employees,
        departments=departments,
        service_types=service_types,
        selected_employee_id=selected_employee_id,
    )


def _employee_from_form(employee_id=None):
    return Employee(
        id=employee_id,
        full_name=request.form.get("full_name", "").strip(),
        position=request.form.get("position", "").strip(),
        role=request.form.get("role", "Сотрудник"),
        department_id=int(request.form.get("department_id") or 0),
        phone=request.form.get("phone", "").strip(),
        email=request.form.get("email", "").strip(),
        status=request.form.get("status", "Активен"),
    )


def _account_from_form(account_id=None):
    return BusinessAccount(
        id=account_id,
        employee_id=int(request.form.get("employee_id") or 0),
        department_id=int(request.form.get("department_id") or 0),
        service_type_id=int(request.form.get("service_type_id") or 0),
        service_name=request.form.get("service_name", "").strip(),
        site_url=request.form.get("site_url", "").strip(),
        login=request.form.get("login", "").strip(),
        password=request.form.get("password", ""),
        email=request.form.get("email", "").strip(),
        comment=request.form.get("comment", "").strip(),
        is_favorite=bool(request.form.get("is_favorite")),
    )


def _validate_account(account):
    if not account.employee_id:
        return "Выберите сотрудника."
    if not account.department_id:
        return "Выберите отдел."
    if not account.service_type_id:
        return "Выберите тип сервиса."
    if not account.service_name:
        return "Название сервиса обязательно."
    if not account.login and not account.email:
        return "Заполните логин или email."
    if not account.password:
        return "Пароль обязателен."
    return ""


if __name__ == "__main__":
    app.run(debug=True)

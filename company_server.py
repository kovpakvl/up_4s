import hashlib
import os
import secrets
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, jsonify, request

from config import DEFAULT_DEPARTMENTS, DEFAULT_SERVICE_TYPES
from secureoffice_service import is_weak_password


BASE_DIR = Path(__file__).resolve().parent
SERVER_DATA_DIR = BASE_DIR / "server_data"
SERVER_DB_PATH = SERVER_DATA_DIR / "secureoffice_server.db"
SERVER_KEY_PATH = SERVER_DATA_DIR / "server.key"
SERVER_BACKUP_DIR = BASE_DIR / "server_backups"
TOKEN_LIFETIME_DAYS = 7

app = Flask(__name__)


@contextmanager
def connection():
    conn = sqlite3.connect(SERVER_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        yield conn
    finally:
        conn.close()


def ensure_server_database() -> None:
    SERVER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS service_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_financial INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                position TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'Сотрудник',
                department_id INTEGER NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Активен',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                access_role TEXT NOT NULL CHECK(access_role IN ('admin', 'employee')),
                employee_id INTEGER UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_hash TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL DEFAULT '',
                department_id INTEGER NOT NULL,
                employee_role TEXT NOT NULL DEFAULT 'Сотрудник',
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                department_id INTEGER NOT NULL,
                service_type_id INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                site_url TEXT NOT NULL DEFAULT '',
                login TEXT NOT NULL DEFAULT '',
                encrypted_password TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                comment TEXT NOT NULL DEFAULT '',
                is_favorite INTEGER NOT NULL DEFAULT 0,
                password_changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (service_type_id) REFERENCES service_types(id)
            );
            CREATE INDEX IF NOT EXISTS idx_accounts_employee ON accounts(employee_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            """
        )
        for name in DEFAULT_DEPARTMENTS:
            conn.execute("INSERT OR IGNORE INTO departments(name) VALUES (?)", (name,))
        financial = {"Банк", "Онлайн-касса", "Бухгалтерия"}
        for name in DEFAULT_SERVICE_TYPES:
            conn.execute(
                "INSERT OR IGNORE INTO service_types(name, is_financial) VALUES (?, ?)",
                (name, int(name in financial)),
            )
        conn.commit()
    _server_crypto()


def _server_crypto() -> Fernet:
    SERVER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SERVER_KEY_PATH.exists():
        SERVER_KEY_PATH.write_bytes(Fernet.generate_key())
    return Fernet(SERVER_KEY_PATH.read_bytes())


def _password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 390_000
    ).hex()


def _validate_password(password: str) -> str:
    if len(password) < 10:
        return "Пароль должен содержать не менее 10 символов."
    checks = [
        any(ch.islower() for ch in password),
        any(ch.isupper() for ch in password),
        any(ch.isdigit() for ch in password),
        any(not ch.isalnum() for ch in password),
    ]
    if sum(checks) < 3:
        return "Используйте минимум три типа символов."
    return ""


def _hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _user_payload(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "access_role": row["access_role"],
        "employee_id": row["employee_id"],
        "full_name": row["full_name"] if "full_name" in row.keys() else "",
    }


def auth_required(admin: bool = False):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            token = header.removeprefix("Bearer ").strip()
            if not token:
                return jsonify(error="Требуется авторизация."), 401
            with connection() as conn:
                row = conn.execute(
                    """
                    SELECT u.*, e.full_name
                    FROM sessions s
                    JOIN users u ON u.id = s.user_id
                    LEFT JOIN employees e ON e.id = u.employee_id
                    WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1
                    """,
                    (_hash_token(token), _iso(_now())),
                ).fetchone()
            if row is None:
                return jsonify(error="Сессия истекла. Выполните вход снова."), 401
            if admin and row["access_role"] != "admin":
                return jsonify(error="Недостаточно прав."), 403
            request.current_user = dict(row)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def _account_allowed(account: sqlite3.Row) -> bool:
    user = request.current_user
    return user["access_role"] == "admin" or account["employee_id"] == user["employee_id"]


@app.get("/api/status")
def status():
    ensure_server_database()
    with connection() as conn:
        initialized = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None
    return jsonify(name="SecureOffice Company Server", initialized=initialized)


@app.post("/api/setup-admin")
def setup_admin():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    full_name = str(data.get("full_name", "")).strip()
    error = _validate_password(password)
    if not username or not full_name or error:
        return jsonify(error=error or "Заполните имя администратора и логин."), 400
    with connection() as conn:
        if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            return jsonify(error="Сервер уже настроен."), 409
        department = conn.execute(
            "SELECT id FROM departments WHERE name = 'Руководство'"
        ).fetchone()
        cursor = conn.execute(
            """
            INSERT INTO employees(full_name, position, role, department_id, status)
            VALUES (?, 'Администратор системы', 'Администратор', ?, 'Активен')
            """,
            (full_name, department["id"]),
        )
        salt = os.urandom(16)
        conn.execute(
            """
            INSERT INTO users(username, password_hash, salt, access_role, employee_id)
            VALUES (?, ?, ?, 'admin', ?)
            """,
            (username, _password_hash(password, salt), salt.hex(), cursor.lastrowid),
        )
        conn.commit()
    return jsonify(message="Администратор создан."), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with connection() as conn:
        row = conn.execute(
            """
            SELECT u.*, e.full_name
            FROM users u LEFT JOIN employees e ON e.id = u.employee_id
            WHERE u.username = ? AND u.is_active = 1
            """,
            (username,),
        ).fetchone()
        if row is None:
            return jsonify(error="Неверный логин или пароль."), 401
        salt = bytes.fromhex(row["salt"])
        if not secrets.compare_digest(row["password_hash"], _password_hash(password, salt)):
            return jsonify(error="Неверный логин или пароль."), 401
        token = secrets.token_urlsafe(32)
        expires = _now() + timedelta(days=TOKEN_LIFETIME_DAYS)
        conn.execute(
            "INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_hash_token(token), row["id"], _iso(expires)),
        )
        conn.commit()
    return jsonify(token=token, user=_user_payload(row))


@app.post("/api/logout")
@auth_required()
def logout():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    with connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
        conn.commit()
    return jsonify(message="Выход выполнен.")


@app.get("/api/departments")
@auth_required()
def departments():
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.name, COUNT(e.id) AS employee_count
            FROM departments d LEFT JOIN employees e ON e.department_id = d.id
            GROUP BY d.id ORDER BY d.name COLLATE NOCASE
            """
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/service-types")
@auth_required()
def service_types():
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM service_types ORDER BY is_financial DESC, name COLLATE NOCASE"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/employees")
@auth_required()
def employees():
    user = request.current_user
    query = request.args.get("q", "").strip()
    department_id = request.args.get("department_id", type=int)
    clauses, params = [], []
    if user["access_role"] != "admin":
        clauses.append("e.id = ?")
        params.append(user["employee_id"])
    if department_id:
        clauses.append("e.department_id = ?")
        params.append(department_id)
    if query:
        like = f"%{query}%"
        clauses.append("(e.full_name LIKE ? OR e.position LIKE ? OR e.email LIKE ?)")
        params.extend([like, like, like])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT e.*, d.name AS department_name, COUNT(a.id) AS account_count
            FROM employees e JOIN departments d ON d.id=e.department_id
            LEFT JOIN accounts a ON a.employee_id=e.id
            {where}
            GROUP BY e.id ORDER BY e.status='Уволен', e.full_name COLLATE NOCASE
            """,
            params,
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/employees/<int:employee_id>")
@auth_required()
def employee_detail(employee_id):
    user = request.current_user
    if user["access_role"] != "admin" and employee_id != user["employee_id"]:
        return jsonify(error="Недостаточно прав."), 403
    with connection() as conn:
        row = conn.execute(
            """
            SELECT e.*, d.name AS department_name
            FROM employees e JOIN departments d ON d.id=e.department_id
            WHERE e.id=?
            """,
            (employee_id,),
        ).fetchone()
    return (jsonify(dict(row)), 200) if row else (jsonify(error="Не найдено."), 404)


@app.post("/api/employees")
@auth_required(admin=True)
def add_employee():
    data = request.get_json(silent=True) or {}
    if not str(data.get("full_name", "")).strip():
        return jsonify(error="ФИО обязательно."), 400
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO employees(full_name, position, role, department_id, phone, email, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(data["full_name"]).strip(),
                str(data.get("position", "")).strip(),
                str(data.get("role", "Сотрудник")),
                int(data["department_id"]),
                str(data.get("phone", "")).strip(),
                str(data.get("email", "")).strip(),
                str(data.get("status", "Активен")),
            ),
        )
        conn.commit()
    return jsonify(id=cursor.lastrowid), 201


@app.put("/api/employees/<int:employee_id>")
@auth_required(admin=True)
def update_employee(employee_id):
    data = request.get_json(silent=True) or {}
    with connection() as conn:
        conn.execute(
            """
            UPDATE employees SET full_name=?, position=?, role=?, department_id=?,
                phone=?, email=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            """,
            (
                str(data["full_name"]).strip(),
                str(data.get("position", "")).strip(),
                str(data.get("role", "Сотрудник")),
                int(data["department_id"]),
                str(data.get("phone", "")).strip(),
                str(data.get("email", "")).strip(),
                str(data.get("status", "Активен")),
                employee_id,
            ),
        )
        conn.execute(
            "UPDATE accounts SET department_id=?, updated_at=CURRENT_TIMESTAMP WHERE employee_id=?",
            (int(data["department_id"]), employee_id),
        )
        conn.commit()
    return jsonify(message="Сотрудник обновлён.")


@app.delete("/api/employees/<int:employee_id>")
@auth_required(admin=True)
def delete_employee(employee_id):
    with connection() as conn:
        if conn.execute(
            "SELECT 1 FROM accounts WHERE employee_id=? LIMIT 1", (employee_id,)
        ).fetchone():
            return jsonify(error="У сотрудника есть закреплённые аккаунты."), 409
        if conn.execute(
            "SELECT 1 FROM users WHERE employee_id=? LIMIT 1", (employee_id,)
        ).fetchone():
            return jsonify(error="Сотрудник зарегистрирован в системе."), 409
        conn.execute("DELETE FROM employees WHERE id=?", (employee_id,))
        conn.commit()
    return jsonify(message="Сотрудник удалён.")


@app.post("/api/invitations")
@auth_required(admin=True)
def create_invitation():
    data = request.get_json(silent=True) or {}
    code = secrets.token_urlsafe(9).upper()
    expires = _now() + timedelta(days=3)
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO invitations(code_hash, email, department_id, employee_role,
                                    expires_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _hash_token(code),
                str(data.get("email", "")).strip(),
                int(data["department_id"]),
                str(data.get("employee_role", "Сотрудник")),
                _iso(expires),
                request.current_user["id"],
            ),
        )
        conn.commit()
    return jsonify(code=code, expires_at=_iso(expires)), 201


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    code = str(data.get("invite_code", "")).strip().upper()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    full_name = str(data.get("full_name", "")).strip()
    error = _validate_password(password)
    if not code or not username or not full_name or error:
        return jsonify(error=error or "Заполните обязательные поля."), 400
    with connection() as conn:
        invite = conn.execute(
            """
            SELECT * FROM invitations
            WHERE code_hash=? AND used_at IS NULL AND expires_at>?
            """,
            (_hash_token(code), _iso(_now())),
        ).fetchone()
        if invite is None:
            return jsonify(error="Код приглашения недействителен или истёк."), 400
        if conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
            return jsonify(error="Такой логин уже занят."), 409
        employee = conn.execute(
            "SELECT id FROM employees WHERE email=? AND email<>'' LIMIT 1",
            (invite["email"],),
        ).fetchone()
        if employee:
            employee_id = employee["id"]
            if conn.execute(
                "SELECT 1 FROM users WHERE employee_id=?", (employee_id,)
            ).fetchone():
                return jsonify(error="Этот сотрудник уже зарегистрирован."), 409
            conn.execute(
                """
                UPDATE employees SET full_name=?, department_id=?, role=?,
                    phone=?, status='Активен', updated_at=CURRENT_TIMESTAMP WHERE id=?
                """,
                (
                    full_name,
                    invite["department_id"],
                    invite["employee_role"],
                    str(data.get("phone", "")).strip(),
                    employee_id,
                ),
            )
        else:
            cursor = conn.execute(
                """
                INSERT INTO employees(full_name, role, department_id, phone, email, status)
                VALUES (?, ?, ?, ?, ?, 'Активен')
                """,
                (
                    full_name,
                    invite["employee_role"],
                    invite["department_id"],
                    str(data.get("phone", "")).strip(),
                    invite["email"],
                ),
            )
            employee_id = cursor.lastrowid
        salt = os.urandom(16)
        conn.execute(
            """
            INSERT INTO users(username, password_hash, salt, access_role, employee_id)
            VALUES (?, ?, ?, 'employee', ?)
            """,
            (username, _password_hash(password, salt), salt.hex(), employee_id),
        )
        conn.execute(
            "UPDATE invitations SET used_at=CURRENT_TIMESTAMP WHERE id=?", (invite["id"],)
        )
        conn.commit()
    return jsonify(message="Регистрация завершена."), 201


@app.post("/api/backup")
@auth_required(admin=True)
def backup_server():
    SERVER_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    db_target = SERVER_BACKUP_DIR / f"company_{stamp}.db"
    key_target = SERVER_BACKUP_DIR / f"company_{stamp}.key"
    with closing(sqlite3.connect(SERVER_DB_PATH)) as source, closing(
        sqlite3.connect(db_target)
    ) as target:
        source.backup(target)
    key_target.write_bytes(SERVER_KEY_PATH.read_bytes())
    return jsonify(database=str(db_target), key=str(key_target))


@app.get("/api/accounts")
@auth_required()
def accounts():
    user = request.current_user
    query = request.args.get("q", "").strip()
    employee_id = request.args.get("employee_id", type=int)
    department_id = request.args.get("department_id", type=int)
    clauses, params = [], []
    if user["access_role"] != "admin":
        clauses.append("a.employee_id=?")
        params.append(user["employee_id"])
    elif employee_id:
        clauses.append("a.employee_id=?")
        params.append(employee_id)
    if department_id:
        clauses.append("a.department_id=?")
        params.append(department_id)
    if query:
        like = f"%{query}%"
        clauses.append(
            "(a.service_name LIKE ? OR a.login LIKE ? OR a.email LIKE ? OR e.full_name LIKE ?)"
        )
        params.extend([like, like, like, like])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT a.id,a.employee_id,a.department_id,a.service_type_id,a.service_name,
                   a.site_url,a.login,a.email,a.is_favorite,a.password_changed_at,a.updated_at,
                   e.full_name employee_name,d.name department_name,
                   s.name service_type_name,s.is_financial
            FROM accounts a JOIN employees e ON e.id=a.employee_id
            JOIN departments d ON d.id=a.department_id
            JOIN service_types s ON s.id=a.service_type_id
            {where}
            ORDER BY s.is_financial DESC,a.is_favorite DESC,a.updated_at DESC
            """,
            params,
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/accounts/<int:account_id>")
@auth_required()
def account_detail(account_id):
    with connection() as conn:
        row = conn.execute(
            """
            SELECT a.*,e.full_name employee_name,d.name department_name,
                   s.name service_type_name,s.is_financial
            FROM accounts a JOIN employees e ON e.id=a.employee_id
            JOIN departments d ON d.id=a.department_id
            JOIN service_types s ON s.id=a.service_type_id WHERE a.id=?
            """,
            (account_id,),
        ).fetchone()
    if row is None:
        return jsonify(error="Аккаунт не найден."), 404
    if not _account_allowed(row):
        return jsonify(error="Недостаточно прав."), 403
    payload = dict(row)
    try:
        payload["password"] = _server_crypto().decrypt(
            payload.pop("encrypted_password").encode("ascii")
        ).decode("utf-8")
    except InvalidToken:
        return jsonify(error="Не удалось расшифровать пароль."), 500
    payload["is_weak"] = is_weak_password(payload["password"])
    return jsonify(payload)


def _account_values(data: dict, existing_employee_id: int | None = None):
    user = request.current_user
    employee_id = (
        user["employee_id"]
        if user["access_role"] != "admin"
        else int(data.get("employee_id") or existing_employee_id or 0)
    )
    with connection() as conn:
        employee = conn.execute(
            "SELECT id,department_id FROM employees WHERE id=?", (employee_id,)
        ).fetchone()
    if employee is None:
        raise ValueError("Выберите сотрудника.")
    return employee_id, employee["department_id"]


@app.post("/api/accounts")
@auth_required()
def add_account():
    data = request.get_json(silent=True) or {}
    try:
        employee_id, department_id = _account_values(data)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    password = str(data.get("password", ""))
    if not str(data.get("service_name", "")).strip() or not password:
        return jsonify(error="Название сервиса и пароль обязательны."), 400
    encrypted = _server_crypto().encrypt(password.encode("utf-8")).decode("ascii")
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO accounts(employee_id,department_id,service_type_id,service_name,
                site_url,login,encrypted_password,email,comment,is_favorite)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                employee_id,
                department_id,
                int(data["service_type_id"]),
                str(data["service_name"]).strip(),
                str(data.get("site_url", "")).strip(),
                str(data.get("login", "")).strip(),
                encrypted,
                str(data.get("email", "")).strip(),
                str(data.get("comment", "")).strip(),
                int(bool(data.get("is_favorite"))),
            ),
        )
        conn.commit()
    return jsonify(id=cursor.lastrowid), 201


@app.put("/api/accounts/<int:account_id>")
@auth_required()
def update_account(account_id):
    data = request.get_json(silent=True) or {}
    with connection() as conn:
        existing = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    if existing is None:
        return jsonify(error="Аккаунт не найден."), 404
    if not _account_allowed(existing):
        return jsonify(error="Недостаточно прав."), 403
    try:
        employee_id, department_id = _account_values(data, existing["employee_id"])
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    encrypted = _server_crypto().encrypt(
        str(data["password"]).encode("utf-8")
    ).decode("ascii")
    changed_sql = (
        "password_changed_at=CURRENT_TIMESTAMP,"
        if bool(data.get("password_changed"))
        else ""
    )
    with connection() as conn:
        conn.execute(
            f"""
            UPDATE accounts SET employee_id=?,department_id=?,service_type_id=?,
                service_name=?,site_url=?,login=?,encrypted_password=?,email=?,comment=?,
                is_favorite=?,{changed_sql}updated_at=CURRENT_TIMESTAMP WHERE id=?
            """,
            (
                employee_id,
                department_id,
                int(data["service_type_id"]),
                str(data["service_name"]).strip(),
                str(data.get("site_url", "")).strip(),
                str(data.get("login", "")).strip(),
                encrypted,
                str(data.get("email", "")).strip(),
                str(data.get("comment", "")).strip(),
                int(bool(data.get("is_favorite"))),
                account_id,
            ),
        )
        conn.commit()
    return jsonify(message="Аккаунт обновлён.")


@app.delete("/api/accounts/<int:account_id>")
@auth_required()
def delete_account(account_id):
    with connection() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if row is None:
            return jsonify(error="Аккаунт не найден."), 404
        if not _account_allowed(row):
            return jsonify(error="Недостаточно прав."), 403
        conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        conn.commit()
    return jsonify(message="Аккаунт удалён.")


@app.get("/api/stats")
@auth_required()
def stats():
    user = request.current_user
    employee_clause = "" if user["access_role"] == "admin" else "WHERE employee_id=?"
    params = [] if user["access_role"] == "admin" else [user["employee_id"]]
    with connection() as conn:
        employees_count = (
            conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
            if user["access_role"] == "admin"
            else 1
        )
        rows = conn.execute(
            f"SELECT encrypted_password,password_changed_at,service_type_id FROM accounts {employee_clause}",
            params,
        ).fetchall()
        financial_ids = {
            row["id"]
            for row in conn.execute(
                "SELECT id FROM service_types WHERE is_financial=1"
            ).fetchall()
        }
    weak = stale = financial = 0
    threshold = _now() - timedelta(days=90)
    crypto = _server_crypto()
    for row in rows:
        try:
            password = crypto.decrypt(row["encrypted_password"].encode("ascii")).decode()
            weak += int(is_weak_password(password))
        except InvalidToken:
            weak += 1
        financial += int(row["service_type_id"] in financial_ids)
        try:
            changed = datetime.fromisoformat(row["password_changed_at"]).replace(
                tzinfo=timezone.utc
            )
            stale += int(changed < threshold)
        except ValueError:
            stale += 1
    return jsonify(
        employees=employees_count,
        accounts=len(rows),
        financial=financial,
        weak_passwords=weak,
        stale_passwords=stale,
    )


ensure_server_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)

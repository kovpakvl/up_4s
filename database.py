import sqlite3
from contextlib import contextmanager

from config import DATA_DIR, DB_PATH, DEFAULT_DEPARTMENTS, DEFAULT_SERVICE_TYPES


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                master_password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS service_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_financial INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
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
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                department_id INTEGER,
                service_type_id INTEGER,
                service_name TEXT NOT NULL,
                site_url TEXT DEFAULT '',
                login TEXT DEFAULT '',
                encrypted_password TEXT NOT NULL,
                email TEXT DEFAULT '',
                comment TEXT DEFAULT '',
                category TEXT DEFAULT '',
                is_favorite INTEGER NOT NULL DEFAULT 0,
                password_changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (service_type_id) REFERENCES service_types(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT NOT NULL UNIQUE,
                setting_value TEXT NOT NULL
            )
            """
        )
        _migrate_password_entries(conn)
        _seed_reference_data(conn)
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        yield conn
    finally:
        conn.close()


def has_user() -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = 1").fetchone()
        return row is not None


def reset_vault() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM password_entries")
        conn.execute("DELETE FROM employees")
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM settings")
        conn.commit()


def _migrate_password_entries(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(password_entries)").fetchall()
    }
    migrations = {
        "employee_id": "ALTER TABLE password_entries ADD COLUMN employee_id INTEGER",
        "department_id": "ALTER TABLE password_entries ADD COLUMN department_id INTEGER",
        "service_type_id": "ALTER TABLE password_entries ADD COLUMN service_type_id INTEGER",
        "password_changed_at": "ALTER TABLE password_entries ADD COLUMN password_changed_at TEXT",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)
    conn.execute(
        """
        UPDATE password_entries
        SET password_changed_at = COALESCE(password_changed_at, updated_at, CURRENT_TIMESTAMP)
        WHERE password_changed_at IS NULL OR password_changed_at = ''
        """
    )


def _seed_reference_data(conn: sqlite3.Connection) -> None:
    for name in DEFAULT_DEPARTMENTS:
        conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
    financial = {"Банк", "Онлайн-касса", "Бухгалтерия"}
    for name in DEFAULT_SERVICE_TYPES:
        conn.execute(
            """
            INSERT OR IGNORE INTO service_types (name, is_financial)
            VALUES (?, ?)
            """,
            (name, int(name in financial)),
        )

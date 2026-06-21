from dataclasses import dataclass
from typing import Optional

from config import FINANCIAL_SERVICE_TYPES
from crypto_service import CryptoService
from database import get_connection


@dataclass
class BusinessAccount:
    id: Optional[int]
    employee_id: int
    department_id: int
    service_type_id: int
    service_name: str
    site_url: str
    login: str
    password: str
    email: str
    comment: str
    is_favorite: bool = False


def is_weak_password(password: str) -> bool:
    if len(password) < 10:
        return True
    checks = [
        any(ch.islower() for ch in password),
        any(ch.isupper() for ch in password),
        any(ch.isdigit() for ch in password),
        any(not ch.isalnum() for ch in password),
    ]
    return sum(checks) < 3


class SecureOfficeService:
    def __init__(self, crypto: CryptoService):
        self.crypto = crypto

    def dashboard_stats(self) -> dict:
        with get_connection() as conn:
            employees = conn.execute("SELECT COUNT(*) AS total FROM employees").fetchone()
            accounts = conn.execute("SELECT COUNT(*) AS total FROM password_entries").fetchone()
            financial = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM password_entries p
                JOIN service_types s ON s.id = p.service_type_id
                WHERE s.is_financial = 1
                """
            ).fetchone()
            stale = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM password_entries
                WHERE password_changed_at < datetime('now', '-90 days')
                """
            ).fetchone()
            rows = conn.execute(
                "SELECT encrypted_password FROM password_entries"
            ).fetchall()
        weak_passwords = 0
        for row in rows:
            try:
                if is_weak_password(self.crypto.decrypt(row["encrypted_password"])):
                    weak_passwords += 1
            except ValueError:
                weak_passwords += 1
        return {
            "employees": employees["total"],
            "accounts": accounts["total"],
            "financial": financial["total"],
            "weak_passwords": weak_passwords,
            "stale_passwords": stale["total"],
        }

    def list_accounts(
        self,
        employee_id: Optional[int] = None,
        query: str = "",
        department_id: Optional[int] = None,
    ) -> list:
        clauses = []
        params = []
        if employee_id:
            clauses.append("p.employee_id = ?")
            params.append(employee_id)
        if department_id:
            clauses.append("p.department_id = ?")
            params.append(department_id)
        if query:
            like = f"%{query.strip()}%"
            clauses.append(
                """
                (p.service_name LIKE ?
                 OR p.site_url LIKE ?
                 OR p.login LIKE ?
                 OR p.email LIKE ?
                 OR e.full_name LIKE ?
                 OR d.name LIKE ?
                 OR s.name LIKE ?)
                """
            )
            params.extend([like, like, like, like, like, like, like])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT p.id, p.service_name, p.site_url, p.login, p.email,
                       p.is_favorite, p.password_changed_at, p.updated_at,
                       e.full_name AS employee_name,
                       d.name AS department_name,
                       s.name AS service_type_name,
                       s.is_financial
                FROM password_entries p
                JOIN employees e ON e.id = p.employee_id
                JOIN departments d ON d.id = p.department_id
                JOIN service_types s ON s.id = p.service_type_id
                {where}
                ORDER BY s.is_financial DESC, p.is_favorite DESC,
                         p.updated_at DESC, p.service_name COLLATE NOCASE
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_account(self, account_id: int) -> Optional[dict]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT p.*, e.full_name AS employee_name,
                       d.name AS department_name,
                       s.name AS service_type_name,
                       s.is_financial
                FROM password_entries p
                JOIN employees e ON e.id = p.employee_id
                JOIN departments d ON d.id = p.department_id
                JOIN service_types s ON s.id = p.service_type_id
                WHERE p.id = ?
                """,
                (account_id,),
            ).fetchone()
        if row is None:
            return None
        account = dict(row)
        account["password"] = self.crypto.decrypt(account["encrypted_password"])
        account["is_weak"] = is_weak_password(account["password"])
        return account

    def add_account(self, account: BusinessAccount) -> int:
        encrypted_password = self.crypto.encrypt(account.password)
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO password_entries (
                    employee_id, department_id, service_type_id, service_name,
                    site_url, login, encrypted_password, email, comment,
                    category, is_favorite, password_changed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, CURRENT_TIMESTAMP)
                """,
                (
                    account.employee_id,
                    account.department_id,
                    account.service_type_id,
                    account.service_name,
                    account.site_url,
                    account.login,
                    encrypted_password,
                    account.email,
                    account.comment,
                    int(account.is_favorite),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def update_account(self, account: BusinessAccount, password_changed: bool) -> None:
        if account.id is None:
            raise ValueError("Нельзя обновить аккаунт без id.")
        encrypted_password = self.crypto.encrypt(account.password)
        password_changed_sql = (
            "password_changed_at = CURRENT_TIMESTAMP,"
            if password_changed
            else ""
        )
        with get_connection() as conn:
            conn.execute(
                f"""
                UPDATE password_entries
                SET employee_id = ?,
                    department_id = ?,
                    service_type_id = ?,
                    service_name = ?,
                    site_url = ?,
                    login = ?,
                    encrypted_password = ?,
                    email = ?,
                    comment = ?,
                    is_favorite = ?,
                    {password_changed_sql}
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    account.employee_id,
                    account.department_id,
                    account.service_type_id,
                    account.service_name,
                    account.site_url,
                    account.login,
                    encrypted_password,
                    account.email,
                    account.comment,
                    int(account.is_favorite),
                    account.id,
                ),
            )
            conn.commit()

    def delete_account(self, account_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM password_entries WHERE id = ?", (account_id,))
            conn.commit()


def is_financial_service(name: str) -> bool:
    return name in FINANCIAL_SERVICE_TYPES

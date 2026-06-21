from typing import Any

from ..db import Database


class PasswordEntryRepository:
    def __init__(self, database: Database):
        self.database = database

    def list_entries(self, employee_id: int) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, service_name, site_url, login, encrypted_password,
                       comment, is_favorite, password_changed_at, created_at, updated_at
                FROM password_entries
                WHERE employee_id = %s
                ORDER BY is_favorite DESC, updated_at DESC, service_name
                """,
                (employee_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_all_entries(self) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.employee_id, p.service_name, p.site_url, p.login,
                       p.encrypted_password, p.comment, p.is_favorite,
                       p.password_changed_at, p.created_at, p.updated_at,
                       e.full_name AS employee_name
                FROM password_entries p
                JOIN employees e ON e.id = p.employee_id
                ORDER BY p.updated_at DESC, p.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_entry(self, employee_id: int, entry_id: int) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT id, employee_id, service_name, site_url, login,
                       encrypted_password, comment, is_favorite,
                       password_changed_at, created_at, updated_at
                FROM password_entries
                WHERE id = %s AND employee_id = %s
                """,
                (entry_id, employee_id),
            ).fetchone()
        return dict(row) if row else None

    def get_entry_by_id(self, entry_id: int) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT p.id, p.employee_id, p.service_name, p.site_url, p.login,
                       p.encrypted_password, p.comment, p.is_favorite,
                       p.password_changed_at, p.created_at, p.updated_at,
                       e.full_name AS employee_name
                FROM password_entries p
                JOIN employees e ON e.id = p.employee_id
                WHERE p.id = %s
                """,
                (entry_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_entry(
        self,
        employee_id: int,
        service_name: str,
        site_url: str,
        login: str,
        encrypted_password: str,
        comment: str,
        is_favorite: bool,
        created_by: int,
    ) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO password_entries(
                    employee_id, service_name, site_url, login, encrypted_password,
                    comment, is_favorite, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, employee_id, service_name, site_url, login,
                          encrypted_password, comment, is_favorite,
                          password_changed_at, created_at, updated_at
                """,
                (
                    employee_id,
                    service_name,
                    site_url,
                    login,
                    encrypted_password,
                    comment,
                    is_favorite,
                    created_by,
                ),
            ).fetchone()
            conn.commit()
        return dict(row)

    def update_entry(
        self,
        employee_id: int,
        entry_id: int,
        service_name: str,
        site_url: str,
        login: str,
        encrypted_password: str,
        comment: str,
        is_favorite: bool,
        password_changed: bool,
    ) -> dict[str, Any] | None:
        password_changed_sql = "password_changed_at = now()," if password_changed else ""
        with self.database.connection() as conn:
            row = conn.execute(
                f"""
                UPDATE password_entries
                SET service_name = %s,
                    site_url = %s,
                    login = %s,
                    encrypted_password = %s,
                    comment = %s,
                    is_favorite = %s,
                    {password_changed_sql}
                    updated_at = now()
                WHERE id = %s AND employee_id = %s
                RETURNING id, employee_id, service_name, site_url, login,
                          encrypted_password, comment, is_favorite,
                          password_changed_at, created_at, updated_at
                """,
                (
                    service_name,
                    site_url,
                    login,
                    encrypted_password,
                    comment,
                    is_favorite,
                    entry_id,
                    employee_id,
                ),
            ).fetchone()
            conn.commit()
        return dict(row) if row else None

    def delete_entry(self, employee_id: int, entry_id: int) -> bool:
        with self.database.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM password_entries WHERE id = %s AND employee_id = %s",
                (entry_id, employee_id),
            )
            conn.commit()
        return cursor.rowcount > 0

    def delete_entry_by_id(self, entry_id: int) -> bool:
        with self.database.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM password_entries WHERE id = %s",
                (entry_id,),
            )
            conn.commit()
        return cursor.rowcount > 0

    def add_history(
        self,
        entry_id: int,
        encrypted_password: str,
        changed_by: int,
    ) -> None:
        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO password_history(entry_id, encrypted_password, changed_by)
                VALUES (%s, %s, %s)
                """,
                (entry_id, encrypted_password, changed_by),
            )
            conn.commit()

    def list_history(self, employee_id: int, entry_id: int) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT h.id, h.entry_id, h.encrypted_password, h.created_at,
                       u.display_name AS changed_by_name
                FROM password_history h
                JOIN password_entries p ON p.id = h.entry_id
                LEFT JOIN users u ON u.id = h.changed_by
                WHERE h.entry_id = %s AND p.employee_id = %s
                ORDER BY h.created_at DESC, h.id DESC
                """,
                (entry_id, employee_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_history_by_entry_id(self, entry_id: int) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT h.id, h.entry_id, h.encrypted_password, h.created_at,
                       u.display_name AS changed_by_name
                FROM password_history h
                LEFT JOIN users u ON u.id = h.changed_by
                WHERE h.entry_id = %s
                ORDER BY h.created_at DESC, h.id DESC
                """,
                (entry_id,),
            ).fetchall()
        return [dict(row) for row in rows]

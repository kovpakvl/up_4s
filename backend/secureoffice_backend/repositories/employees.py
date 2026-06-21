from datetime import datetime
from typing import Any

from ..db import Database


class EmployeeRepository:
    def __init__(self, database: Database):
        self.database = database

    def create_employee(
        self,
        full_name: str,
        email: str = "",
        phone: str = "",
        department_id: int | None = None,
        position_id: int | None = None,
    ) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO employees(full_name, email, phone, department_id, position_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, full_name, email, phone, department_id, position_id, status
                """,
                (full_name, email, phone, department_id, position_id),
            ).fetchone()
            conn.commit()
        return dict(row)

    def list_employees(self) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT e.id, e.full_name, e.email, e.phone, e.status,
                       e.department_id, e.position_id,
                       d.name AS department_name,
                       p.name AS position_name,
                       e.created_at, e.updated_at,
                       u.id IS NOT NULL AS has_user,
                       latest_key.expires_at AS activation_expires_at,
                       latest_key.used_at AS activation_used_at
                FROM employees e
                LEFT JOIN departments d ON d.id = e.department_id
                LEFT JOIN positions p ON p.id = e.position_id
                LEFT JOIN users u ON u.employee_id = e.id
                LEFT JOIN LATERAL (
                    SELECT expires_at, used_at
                    FROM activation_keys k
                    WHERE k.employee_id = e.id
                    ORDER BY k.created_at DESC, k.id DESC
                    LIMIT 1
                ) latest_key ON true
                ORDER BY e.created_at DESC, e.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def list_departments(self) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            departments = conn.execute(
                """
                SELECT id, name, created_at
                FROM departments
                ORDER BY name
                """
            ).fetchall()
            positions = conn.execute(
                """
                SELECT id, department_id, name, created_at
                FROM positions
                ORDER BY name
                """
            ).fetchall()
        grouped: dict[int, list[dict[str, Any]]] = {}
        for position in positions:
            item = dict(position)
            grouped.setdefault(item["department_id"], []).append(item)
        return [
            {**dict(department), "positions": grouped.get(department["id"], [])}
            for department in departments
        ]

    def create_department(self, name: str) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO departments(name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id, name, created_at
                """,
                (name,),
            ).fetchone()
            conn.commit()
        return {**dict(row), "positions": []}

    def create_position(self, department_id: int, name: str) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO positions(department_id, name)
                VALUES (%s, %s)
                ON CONFLICT (department_id, name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id, department_id, name, created_at
                """,
                (department_id, name),
            ).fetchone()
            conn.commit()
        return dict(row)

    def department_exists(self, department_id: int) -> bool:
        with self.database.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM departments WHERE id = %s LIMIT 1",
                (department_id,),
            ).fetchone()
        return row is not None

    def find_position(self, position_id: int) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT id, department_id, name
                FROM positions
                WHERE id = %s
                """,
                (position_id,),
            ).fetchone()
        return dict(row) if row else None

    def find_employee_by_id(self, employee_id: int) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT e.id, e.full_name, e.email, e.phone, e.status,
                       e.department_id, e.position_id,
                       d.name AS department_name,
                       p.name AS position_name
                FROM employees e
                LEFT JOIN departments d ON d.id = e.department_id
                LEFT JOIN positions p ON p.id = e.position_id
                WHERE e.id = %s
                """,
                (employee_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_employee_contacts(
        self,
        employee_id: int,
        *,
        email: str,
        phone: str,
    ) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                UPDATE employees
                SET email = %s, phone = %s, updated_at = now()
                WHERE id = %s
                RETURNING id, full_name, email, phone, status,
                          department_id, position_id
                """,
                (email, phone, employee_id),
            ).fetchone()
            conn.commit()
        return dict(row) if row else None

    def employee_has_user(self, employee_id: int) -> bool:
        with self.database.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE employee_id = %s LIMIT 1",
                (employee_id,),
            ).fetchone()
        return row is not None

    def employee_exists(self, employee_id: int) -> bool:
        with self.database.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM employees WHERE id = %s LIMIT 1",
                (employee_id,),
            ).fetchone()
        return row is not None

    def create_activation_key(
        self,
        employee_id: int,
        code_hash: str,
        expires_at: datetime,
        created_by: int,
    ) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO activation_keys(employee_id, code_hash, expires_at, created_by)
                VALUES (%s, %s, %s, %s)
                RETURNING id, employee_id, expires_at, used_at
                """,
                (employee_id, code_hash, expires_at, created_by),
            ).fetchone()
            conn.commit()
        return dict(row)

    def find_activation_key(self, code_hash: str) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT k.id, k.employee_id, k.expires_at, k.used_at,
                       e.full_name, e.email
                FROM activation_keys k
                JOIN employees e ON e.id = k.employee_id
                WHERE k.code_hash = %s
                """,
                (code_hash,),
            ).fetchone()
        return dict(row) if row else None

    def mark_activation_key_used(self, key_id: int) -> None:
        with self.database.connection() as conn:
            conn.execute(
                "UPDATE activation_keys SET used_at = now() WHERE id = %s",
                (key_id,),
            )
            conn.commit()

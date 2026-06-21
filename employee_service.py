from dataclasses import dataclass
from typing import Optional

from database import get_connection


@dataclass
class Employee:
    id: Optional[int]
    full_name: str
    position: str
    role: str
    department_id: int
    phone: str
    email: str
    status: str


def list_departments() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM departments ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [dict(row) for row in rows]


def list_departments_with_counts() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.name, COUNT(e.id) AS employee_count
            FROM departments d
            LEFT JOIN employees e ON e.department_id = d.id
            GROUP BY d.id
            ORDER BY d.name COLLATE NOCASE
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_department(department_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name FROM departments WHERE id = ?", (department_id,)
        ).fetchone()
    return dict(row) if row else None


def list_service_types() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, is_financial
            FROM service_types
            ORDER BY is_financial DESC, name COLLATE NOCASE
            """
        ).fetchall()
    return [dict(row) for row in rows]


class EmployeeService:
    def list_employees(self, query: str = "", department_id: Optional[int] = None) -> list:
        query = query.strip()
        where_parts = []
        params = []
        if department_id:
            where_parts.append("e.department_id = ?")
            params.append(department_id)
        if query:
            like = f"%{query}%"
            where_parts.append(
                """
                (e.full_name LIKE ?
                 OR e.position LIKE ?
                 OR e.role LIKE ?
                 OR e.email LIKE ?
                 OR d.name LIKE ?)
                """
            )
            params.extend([like, like, like, like, like])
        where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT e.*, d.name AS department_name,
                       COUNT(p.id) AS account_count
                FROM employees e
                JOIN departments d ON d.id = e.department_id
                LEFT JOIN password_entries p ON p.employee_id = e.id
                {where}
                GROUP BY e.id
                ORDER BY e.status = 'Уволен', e.full_name COLLATE NOCASE
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_employee(self, employee_id: int) -> Optional[dict]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT e.*, d.name AS department_name
                FROM employees e
                JOIN departments d ON d.id = e.department_id
                WHERE e.id = ?
                """,
                (employee_id,),
            ).fetchone()
        return dict(row) if row else None

    def add_employee(self, employee: Employee) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO employees (
                    full_name, position, role, department_id, phone, email, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee.full_name,
                    employee.position,
                    employee.role,
                    employee.department_id,
                    employee.phone,
                    employee.email,
                    employee.status,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def update_employee(self, employee: Employee) -> None:
        if employee.id is None:
            raise ValueError("Нельзя обновить сотрудника без id.")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE employees
                SET full_name = ?,
                    position = ?,
                    role = ?,
                    department_id = ?,
                    phone = ?,
                    email = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    employee.full_name,
                    employee.position,
                    employee.role,
                    employee.department_id,
                    employee.phone,
                    employee.email,
                    employee.status,
                    employee.id,
                ),
            )
            conn.execute(
                """
                UPDATE password_entries
                SET department_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE employee_id = ? AND department_id <> ?
                """,
                (employee.department_id, employee.id, employee.department_id),
            )
            conn.commit()

    def delete_employee(self, employee_id: int) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM password_entries WHERE employee_id = ?",
                (employee_id,),
            ).fetchone()
            if row["total"] > 0:
                return False
            conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            conn.commit()
            return True

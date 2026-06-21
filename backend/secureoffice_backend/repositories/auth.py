from datetime import datetime
from typing import Any

from ..db import Database


class AuthRepository:
    def __init__(self, database: Database):
        self.database = database

    def has_admin(self) -> bool:
        with self.database.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE access_role = 'admin' LIMIT 1"
            ).fetchone()
        return row is not None

    def create_admin(
        self,
        username: str,
        display_name: str,
        password_hash: str,
        salt: str,
    ) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users(username, display_name, password_hash, salt, access_role)
                VALUES (%s, %s, %s, %s, 'admin')
                RETURNING id, username, display_name, access_role, employee_id, is_active
                """,
                (username, display_name, password_hash, salt),
            ).fetchone()
            conn.commit()
        return dict(row)

    def create_employee_user(
        self,
        username: str,
        display_name: str,
        password_hash: str,
        salt: str,
        employee_id: int,
    ) -> dict[str, Any]:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users(
                    username, display_name, password_hash, salt, access_role, employee_id
                )
                VALUES (%s, %s, %s, %s, 'employee', %s)
                RETURNING id, username, display_name, access_role, employee_id, is_active
                """,
                (username, display_name, password_hash, salt, employee_id),
            ).fetchone()
            conn.commit()
        return dict(row)

    def find_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT id, username, display_name, password_hash, salt, access_role,
                       employee_id, is_active
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT id, username, display_name, password_hash, salt, access_role,
                       employee_id, is_active
                FROM users
                WHERE lower(username) = lower(%s)
                """,
                (username,),
            ).fetchone()
        return dict(row) if row else None

    def find_user_by_session(self, token_hash: str) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT u.id, u.username, u.display_name, u.password_hash, u.salt,
                       u.access_role, u.employee_id, u.is_active
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                  AND s.expires_at > now()
                  AND u.is_active = true
                """,
                (token_hash,),
            ).fetchone()
        return dict(row) if row else None

    def update_display_name(self, user_id: int, display_name: str) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                UPDATE users
                SET display_name = %s
                WHERE id = %s
                RETURNING id, username, display_name, password_hash, salt,
                          access_role, employee_id, is_active
                """,
                (display_name, user_id),
            ).fetchone()
            conn.commit()
        return dict(row) if row else None

    def create_session(
        self,
        token_hash: str,
        user_id: int,
        expires_at: datetime,
    ) -> None:
        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions(token_hash, user_id, expires_at)
                VALUES (%s, %s, %s)
                """,
                (token_hash, user_id, expires_at),
            )
            conn.commit()

    def write_audit(
        self,
        actor_user_id: int | None,
        event_type: str,
        entity_type: str,
        entity_id: int | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str = "",
    ) -> None:
        from psycopg.types.json import Jsonb

        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_events(
                    actor_user_id, event_type, entity_type, entity_id, details, ip_address
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    actor_user_id,
                    event_type,
                    entity_type,
                    entity_id,
                    Jsonb(details or {}),
                    ip_address,
                ),
            )
            conn.commit()

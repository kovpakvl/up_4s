from typing import Any

from ..db import Database


class AuditRepository:
    def __init__(self, database: Database):
        self.database = database

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT a.id, a.event_type, a.entity_type, a.entity_id,
                       a.details, a.ip_address, a.created_at,
                       u.display_name AS actor_name,
                       u.username AS actor_username
                FROM audit_events a
                LEFT JOIN users u ON u.id = a.actor_user_id
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

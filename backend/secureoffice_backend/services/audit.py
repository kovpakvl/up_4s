from typing import Any

from ..repositories import AuditRepository
from .errors import ServiceError


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def list_events(self, actor_user: dict[str, Any], limit: int = 200) -> list[dict[str, Any]]:
        if not actor_user or actor_user.get("access_role") != "admin":
            raise ServiceError("Недостаточно прав.", 403)
        return self.repository.list_events(min(max(limit, 1), 500))

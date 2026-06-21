from typing import Any

from ..repositories import AuthRepository, PasswordEntryRepository
from .errors import ServiceError
from .passwords import Cipher, parse_entry_values


class AdminPasswordEntryService:
    def __init__(
        self,
        repository: PasswordEntryRepository,
        auth_repository: AuthRepository,
        cipher: Cipher,
    ):
        self.repository = repository
        self.auth_repository = auth_repository
        self.cipher = cipher

    def list_entries(self, actor_user: dict[str, Any]) -> list[dict[str, Any]]:
        _require_admin(actor_user)
        return [self._decrypt_entry(entry) for entry in self.repository.list_all_entries()]

    def create_entries(
        self,
        actor_user: dict[str, Any],
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        _require_admin(actor_user)
        employee_ids = _employee_ids(data.get("employee_ids"))
        values = parse_entry_values(data)
        encrypted_password = self.cipher.encrypt(values["password"])
        entries = []
        for employee_id in employee_ids:
            entry = self.repository.create_entry(
                employee_id=employee_id,
                service_name=values["service_name"],
                site_url=values["site_url"],
                login=values["login"],
                encrypted_password=encrypted_password,
                comment=values["comment"],
                is_favorite=values["is_favorite"],
                created_by=actor_user["id"],
            )
            self.repository.add_history(entry["id"], encrypted_password, actor_user["id"])
            self.auth_repository.write_audit(
                actor_user_id=actor_user["id"],
                event_type="password_entry.created",
                entity_type="password_entry",
                entity_id=entry["id"],
                details={"employee_id": employee_id, "created_by_admin": True},
            )
            entries.append(self._decrypt_entry(entry))
        return entries

    def get_entry(self, actor_user: dict[str, Any], entry_id: int) -> dict[str, Any]:
        _require_admin(actor_user)
        entry = self.repository.get_entry_by_id(entry_id)
        if entry is None:
            raise ServiceError("Запись не найдена.", 404)
        return self._decrypt_entry(entry)

    def update_entry(
        self,
        actor_user: dict[str, Any],
        entry_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        _require_admin(actor_user)
        current = self.repository.get_entry_by_id(entry_id)
        if current is None:
            raise ServiceError("Запись не найдена.", 404)

        values = parse_entry_values(data)
        current_password = self.cipher.decrypt(current["encrypted_password"])
        password_changed = values["password"] != current_password
        encrypted_password = (
            self.cipher.encrypt(values["password"])
            if password_changed
            else current["encrypted_password"]
        )
        entry = self.repository.update_entry(
            employee_id=current["employee_id"],
            entry_id=entry_id,
            service_name=values["service_name"],
            site_url=values["site_url"],
            login=values["login"],
            encrypted_password=encrypted_password,
            comment=values["comment"],
            is_favorite=values["is_favorite"],
            password_changed=password_changed,
        )
        if entry is None:
            raise ServiceError("Запись не найдена.", 404)
        if password_changed:
            self.repository.add_history(entry["id"], encrypted_password, actor_user["id"])
        self.auth_repository.write_audit(
            actor_user_id=actor_user["id"],
            event_type="password_entry.updated",
            entity_type="password_entry",
            entity_id=entry["id"],
            details={"password_changed": password_changed, "updated_by_admin": True},
        )
        return self._decrypt_entry(entry)

    def delete_entry(self, actor_user: dict[str, Any], entry_id: int) -> None:
        _require_admin(actor_user)
        if not self.repository.delete_entry_by_id(entry_id):
            raise ServiceError("Запись не найдена.", 404)
        self.auth_repository.write_audit(
            actor_user_id=actor_user["id"],
            event_type="password_entry.deleted",
            entity_type="password_entry",
            entity_id=entry_id,
            details={"deleted_by_admin": True},
        )

    def list_history(
        self,
        actor_user: dict[str, Any],
        entry_id: int,
    ) -> list[dict[str, Any]]:
        _require_admin(actor_user)
        if self.repository.get_entry_by_id(entry_id) is None:
            raise ServiceError("Запись не найдена.", 404)
        return [
            {
                **row,
                "password": self.cipher.decrypt(row["encrypted_password"]),
            }
            for row in self.repository.list_history_by_entry_id(entry_id)
        ]

    def _decrypt_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {**entry, "password": self.cipher.decrypt(entry["encrypted_password"])}


def _employee_ids(value) -> list[int]:
    if not isinstance(value, list) or not value:
        raise ServiceError("Выберите хотя бы одного сотрудника.")
    try:
        return [int(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ServiceError("Некорректный список сотрудников.") from exc


def _require_admin(user: dict[str, Any]) -> None:
    if not user or user.get("access_role") != "admin":
        raise ServiceError("Недостаточно прав.", 403)

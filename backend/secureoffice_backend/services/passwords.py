from typing import Any, Protocol

from ..repositories import AuthRepository, PasswordEntryRepository
from .errors import ServiceError


class Cipher(Protocol):
    def encrypt(self, value: str) -> str:
        ...

    def decrypt(self, token: str) -> str:
        ...


class PasswordEntryService:
    def __init__(
        self,
        repository: PasswordEntryRepository,
        auth_repository: AuthRepository,
        cipher: Cipher,
    ):
        self.repository = repository
        self.auth_repository = auth_repository
        self.cipher = cipher

    def list_entries(self, user: dict[str, Any]) -> list[dict[str, Any]]:
        employee_id = _employee_id(user)
        return [
            self._decrypt_entry(entry)
            for entry in self.repository.list_entries(employee_id)
        ]

    def get_entry(self, user: dict[str, Any], entry_id: int) -> dict[str, Any]:
        employee_id = _employee_id(user)
        entry = self.repository.get_entry(employee_id, entry_id)
        if entry is None:
            raise ServiceError("Запись не найдена.", 404)
        return self._decrypt_entry(entry)

    def create_entry(self, user: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        employee_id = _employee_id(user)
        values = parse_entry_values(data)
        encrypted_password = self.cipher.encrypt(values["password"])
        entry = self.repository.create_entry(
            employee_id=employee_id,
            service_name=values["service_name"],
            site_url=values["site_url"],
            login=values["login"],
            encrypted_password=encrypted_password,
            comment=values["comment"],
            is_favorite=values["is_favorite"],
            created_by=user["id"],
        )
        self.repository.add_history(entry["id"], encrypted_password, user["id"])
        self.auth_repository.write_audit(
            actor_user_id=user["id"],
            event_type="password_entry.created",
            entity_type="password_entry",
            entity_id=entry["id"],
        )
        return self._decrypt_entry(entry)

    def update_entry(
        self,
        user: dict[str, Any],
        entry_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        employee_id = _employee_id(user)
        current = self.repository.get_entry(employee_id, entry_id)
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
            employee_id=employee_id,
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
            self.repository.add_history(entry["id"], encrypted_password, user["id"])
        self.auth_repository.write_audit(
            actor_user_id=user["id"],
            event_type="password_entry.updated",
            entity_type="password_entry",
            entity_id=entry["id"],
            details={"password_changed": password_changed},
        )
        return self._decrypt_entry(entry)

    def delete_entry(self, user: dict[str, Any], entry_id: int) -> None:
        employee_id = _employee_id(user)
        if not self.repository.delete_entry(employee_id, entry_id):
            raise ServiceError("Запись не найдена.", 404)
        self.auth_repository.write_audit(
            actor_user_id=user["id"],
            event_type="password_entry.deleted",
            entity_type="password_entry",
            entity_id=entry_id,
        )

    def list_history(self, user: dict[str, Any], entry_id: int) -> list[dict[str, Any]]:
        employee_id = _employee_id(user)
        if self.repository.get_entry(employee_id, entry_id) is None:
            raise ServiceError("Запись не найдена.", 404)
        rows = self.repository.list_history(employee_id, entry_id)
        return [
            {
                **row,
                "password": self.cipher.decrypt(row["encrypted_password"]),
            }
            for row in rows
        ]

    def _decrypt_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        return {**entry, "password": self.cipher.decrypt(entry["encrypted_password"])}


def _employee_id(user: dict[str, Any]) -> int:
    if not user or user.get("access_role") != "employee" or not user.get("employee_id"):
        raise ServiceError("Кабинет доступен только сотрудникам.", 403)
    return int(user["employee_id"])


def parse_entry_values(data: dict[str, Any]) -> dict[str, Any]:
    service_name = str(data.get("service_name", "")).strip()
    password = str(data.get("password", ""))
    if not service_name:
        raise ServiceError("Укажите название сервиса.")
    if not password:
        raise ServiceError("Укажите пароль.")
    return {
        "service_name": service_name,
        "site_url": str(data.get("site_url", "")).strip(),
        "login": str(data.get("login", "")).strip(),
        "password": password,
        "comment": str(data.get("comment", "")).strip(),
        "is_favorite": bool(data.get("is_favorite")),
    }

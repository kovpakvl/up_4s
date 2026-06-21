from datetime import UTC, datetime, timedelta
from typing import Any

from ..config import AppConfig
from ..repositories import AuthRepository
from ..security import (
    generate_token,
    hash_password,
    hash_token,
    validate_password,
    verify_password,
)
from .errors import ServiceError


class SetupService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    def status(self) -> dict[str, bool]:
        return {"initialized": self.repository.has_admin()}

    def create_admin(
        self,
        username: str,
        display_name: str,
        password: str,
    ) -> dict[str, Any]:
        username = username.strip()
        display_name = display_name.strip()
        if self.repository.has_admin():
            raise ServiceError("Первый администратор уже создан.", 409)
        if not username or not display_name:
            raise ServiceError("Укажите логин и имя администратора.")
        password_error = validate_password(password)
        if password_error:
            raise ServiceError(password_error)

        password_hash, salt = hash_password(password)
        user = self.repository.create_admin(username, display_name, password_hash, salt)
        self.repository.write_audit(
            actor_user_id=user["id"],
            event_type="admin.created",
            entity_type="user",
            entity_id=user["id"],
        )
        return public_user(user)


class AuthService:
    def __init__(self, repository: AuthRepository, config: AppConfig):
        self.repository = repository
        self.config = config

    def login(self, username: str, password: str, ip_address: str = "") -> dict[str, Any]:
        user = self.repository.find_user_by_username(username.strip())
        if user is None or not user["is_active"]:
            raise ServiceError("Неверный логин или пароль.", 401)
        if not verify_password(password, user["password_hash"], user["salt"]):
            self.repository.write_audit(
                actor_user_id=user["id"],
                event_type="auth.login_failed",
                entity_type="user",
                entity_id=user["id"],
                ip_address=ip_address,
            )
            raise ServiceError("Неверный логин или пароль.", 401)

        token = generate_token()
        expires_at = datetime.now(UTC) + timedelta(hours=self.config.session_ttl_hours)
        self.repository.create_session(hash_token(token), user["id"], expires_at)
        self.repository.write_audit(
            actor_user_id=user["id"],
            event_type="auth.login",
            entity_type="user",
            entity_id=user["id"],
            ip_address=ip_address,
        )
        return {
            "token": token,
            "expires_at": expires_at.isoformat(),
            "user": public_user(user),
        }

    def user_from_token(self, token: str) -> dict[str, Any] | None:
        if not token:
            return None
        user = self.repository.find_user_by_session(hash_token(token))
        return public_user(user) if user else None

    def user_from_id(self, user_id: int | None) -> dict[str, Any] | None:
        if user_id is None:
            return None
        user = self.repository.find_user_by_id(user_id)
        return public_user(user) if user and user["is_active"] else None


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "access_role": user["access_role"],
        "employee_id": user["employee_id"],
        "is_active": user["is_active"],
    }

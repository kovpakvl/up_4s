from datetime import UTC, datetime, timedelta
import secrets
from typing import Any

from ..config import AppConfig
from ..repositories import AuthRepository, EmployeeRepository
from ..security import hash_password, hash_token, validate_password
from .auth import public_user
from .errors import ServiceError


class EmployeeActivationService:
    def __init__(
        self,
        employee_repository: EmployeeRepository,
        auth_repository: AuthRepository,
        config: AppConfig,
    ):
        self.employee_repository = employee_repository
        self.auth_repository = auth_repository
        self.config = config

    def create_employee(
        self,
        actor_user: dict[str, Any],
        full_name: str,
        email: str = "",
        phone: str = "",
        department_id: int | None = None,
        position_id: int | None = None,
    ) -> dict[str, Any]:
        _require_admin(actor_user)
        full_name = full_name.strip()
        if not full_name:
            raise ServiceError("Укажите имя сотрудника.")
        department_id, position_id = self._validate_employee_structure(
            department_id,
            position_id,
        )
        employee = self.employee_repository.create_employee(
            full_name=full_name,
            email=email.strip(),
            phone=phone.strip(),
            department_id=department_id,
            position_id=position_id,
        )
        self.auth_repository.write_audit(
            actor_user_id=actor_user["id"],
            event_type="employee.created",
            entity_type="employee",
            entity_id=employee["id"],
            details={
                "department_id": department_id,
                "position_id": position_id,
            },
        )
        return employee

    def list_employees(self, actor_user: dict[str, Any]) -> list[dict[str, Any]]:
        _require_admin(actor_user)
        return self.employee_repository.list_employees()

    def list_departments(self, actor_user: dict[str, Any]) -> list[dict[str, Any]]:
        _require_admin(actor_user)
        return self.employee_repository.list_departments()

    def create_department(
        self,
        actor_user: dict[str, Any],
        name: str,
    ) -> dict[str, Any]:
        _require_admin(actor_user)
        name = name.strip()
        if not name:
            raise ServiceError("Укажите название отдела.")
        department = self.employee_repository.create_department(name)
        self.auth_repository.write_audit(
            actor_user_id=actor_user["id"],
            event_type="department.created",
            entity_type="department",
            entity_id=department["id"],
            details={"name": department["name"]},
        )
        return department

    def create_position(
        self,
        actor_user: dict[str, Any],
        department_id: int,
        name: str,
    ) -> dict[str, Any]:
        _require_admin(actor_user)
        name = name.strip()
        if not name:
            raise ServiceError("Укажите название должности.")
        if not self.employee_repository.department_exists(department_id):
            raise ServiceError("Отдел не найден.", 404)
        position = self.employee_repository.create_position(department_id, name)
        self.auth_repository.write_audit(
            actor_user_id=actor_user["id"],
            event_type="position.created",
            entity_type="position",
            entity_id=position["id"],
            details={
                "department_id": department_id,
                "name": position["name"],
            },
        )
        return position

    def create_activation_key(
        self,
        actor_user: dict[str, Any],
        employee_id: int,
    ) -> dict[str, Any]:
        _require_admin(actor_user)
        if not self.employee_repository.employee_exists(employee_id):
            raise ServiceError("Сотрудник не найден.", 404)
        if self.employee_repository.employee_has_user(employee_id):
            raise ServiceError("У сотрудника уже есть учётная запись.", 409)

        code = secrets.token_urlsafe(12).replace("-", "").replace("_", "").upper()
        expires_at = datetime.now(UTC) + timedelta(days=self.config.activation_ttl_days)
        key = self.employee_repository.create_activation_key(
            employee_id=employee_id,
            code_hash=hash_token(code),
            expires_at=expires_at,
            created_by=actor_user["id"],
        )
        self.auth_repository.write_audit(
            actor_user_id=actor_user["id"],
            event_type="activation_key.created",
            entity_type="employee",
            entity_id=employee_id,
            details={"key_id": key["id"], "expires_at": expires_at.isoformat()},
        )
        return {
            "code": code,
            "employee_id": employee_id,
            "expires_at": expires_at.isoformat(),
        }

    def _validate_employee_structure(
        self,
        department_id: int | None,
        position_id: int | None,
    ) -> tuple[int | None, int | None]:
        department_id = _optional_int(department_id)
        position_id = _optional_int(position_id)
        if department_id and not self.employee_repository.department_exists(department_id):
            raise ServiceError("Отдел не найден.", 404)
        if not position_id:
            return department_id, None
        position = self.employee_repository.find_position(position_id)
        if position is None:
            raise ServiceError("Должность не найдена.", 404)
        if department_id and position["department_id"] != department_id:
            raise ServiceError("Должность относится к другому отделу.")
        return int(position["department_id"]), position_id

    def activate(self, code: str, username: str, password: str) -> dict[str, Any]:
        code = code.strip().upper()
        username = username.strip()
        key = self.employee_repository.find_activation_key(hash_token(code))
        if key is None or key["used_at"] is not None:
            raise ServiceError("Ключ недействителен.", 400)
        if key["expires_at"] <= datetime.now(UTC):
            raise ServiceError("Срок действия ключа истёк.", 400)
        if self.employee_repository.employee_has_user(key["employee_id"]):
            raise ServiceError("Учётная запись уже активирована.", 409)
        if not username:
            raise ServiceError("Укажите логин.")
        if self.auth_repository.find_user_by_username(username):
            raise ServiceError("Такой логин уже занят.", 409)
        password_error = validate_password(password)
        if password_error:
            raise ServiceError(password_error)

        password_hash, salt = hash_password(password)
        user = self.auth_repository.create_employee_user(
            username=username,
            display_name=key["full_name"],
            password_hash=password_hash,
            salt=salt,
            employee_id=key["employee_id"],
        )
        self.employee_repository.mark_activation_key_used(key["id"])
        self.auth_repository.write_audit(
            actor_user_id=user["id"],
            event_type="employee.activated",
            entity_type="employee",
            entity_id=key["employee_id"],
        )
        return public_user(user)


def _require_admin(user: dict[str, Any]) -> None:
    if not user or user.get("access_role") != "admin":
        raise ServiceError("Недостаточно прав.", 403)


def _optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ServiceError("Некорректный идентификатор отдела или должности.") from exc
    return parsed if parsed > 0 else None

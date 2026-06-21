"""Сервис «Профиль» — чтение и обновление данных текущего пользователя."""
from __future__ import annotations

from typing import Any

from ..repositories import AuthRepository, EmployeeRepository
from .auth import public_user
from .errors import ServiceError


class ProfileService:
    def __init__(
        self,
        auth_repository: AuthRepository,
        employee_repository: EmployeeRepository,
    ):
        self.auth_repository = auth_repository
        self.employee_repository = employee_repository

    def me(self, actor_user: dict[str, Any]) -> dict[str, Any]:
        if not actor_user:
            raise ServiceError("Нужна авторизация.", 401)
        payload = dict(actor_user)
        employee_id = actor_user.get("employee_id")
        payload["employee"] = (
            self.employee_repository.find_employee_by_id(int(employee_id))
            if employee_id
            else None
        )
        return payload

    def update(
        self,
        actor_user: dict[str, Any],
        *,
        display_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any]:
        if not actor_user:
            raise ServiceError("Нужна авторизация.", 401)

        if display_name is not None:
            cleaned = display_name.strip()
            if not cleaned:
                raise ServiceError("Имя не может быть пустым.")
            self.auth_repository.update_display_name(int(actor_user["id"]), cleaned)

        employee_id = actor_user.get("employee_id")
        if employee_id and (email is not None or phone is not None):
            employee = self.employee_repository.find_employee_by_id(int(employee_id))
            if employee is None:
                raise ServiceError("Карточка сотрудника не найдена.", 404)
            new_email = (email if email is not None else employee.get("email", "")).strip()
            new_phone = (phone if phone is not None else employee.get("phone", "")).strip()
            if new_email and ("@" not in new_email or new_email.startswith("@") or new_email.endswith("@")):
                raise ServiceError("Некорректный email.")
            self.employee_repository.update_employee_contacts(
                int(employee_id), email=new_email, phone=new_phone
            )

        # Возвращаем актуальное состояние
        fresh_user = self.auth_repository.find_user_by_id(int(actor_user["id"]))
        if fresh_user is None:
            raise ServiceError("Пользователь не найден.", 404)
        return self.me(public_user(fresh_user))

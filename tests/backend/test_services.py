import pytest

from secureoffice_backend.config import AppConfig
from secureoffice_backend.security import hash_password
from secureoffice_backend.services import AuthService, ServiceError, SetupService


class FakeAuthRepository:
    def __init__(self):
        self.users = {}
        self.sessions = []
        self.audit_events = []

    def has_admin(self):
        return any(user["access_role"] == "admin" for user in self.users.values())

    def create_admin(self, username, display_name, password_hash, salt):
        user = {
            "id": len(self.users) + 1,
            "username": username,
            "display_name": display_name,
            "password_hash": password_hash,
            "salt": salt,
            "access_role": "admin",
            "employee_id": None,
            "is_active": True,
        }
        self.users[username.lower()] = user
        return user

    def find_user_by_username(self, username):
        return self.users.get(username.lower())

    def create_session(self, token_hash, user_id, expires_at):
        self.sessions.append(
            {"token_hash": token_hash, "user_id": user_id, "expires_at": expires_at}
        )

    def write_audit(self, **event):
        self.audit_events.append(event)


def test_setup_service_creates_first_admin():
    repository = FakeAuthRepository()
    service = SetupService(repository)

    user = service.create_admin("admin", "System Admin", "StrongPass123!")

    assert user["username"] == "admin"
    assert user["access_role"] == "admin"
    assert "password_hash" not in user
    assert repository.audit_events[-1]["event_type"] == "admin.created"


def test_setup_service_rejects_second_admin():
    repository = FakeAuthRepository()
    service = SetupService(repository)
    service.create_admin("admin", "System Admin", "StrongPass123!")

    with pytest.raises(ServiceError) as exc_info:
        service.create_admin("second", "Second Admin", "StrongPass123!")

    assert exc_info.value.status_code == 409


def test_auth_service_login_creates_session_and_audit():
    repository = FakeAuthRepository()
    password_hash, salt = hash_password("StrongPass123!")
    repository.create_admin("admin", "System Admin", password_hash, salt)
    service = AuthService(repository, AppConfig(database_url="postgresql://test"))

    payload = service.login("admin", "StrongPass123!", ip_address="127.0.0.1")

    assert payload["token"]
    assert payload["user"]["username"] == "admin"
    assert len(repository.sessions) == 1
    assert repository.audit_events[-1]["event_type"] == "auth.login"


def test_auth_service_login_rejects_wrong_password():
    repository = FakeAuthRepository()
    password_hash, salt = hash_password("StrongPass123!")
    repository.create_admin("admin", "System Admin", password_hash, salt)
    service = AuthService(repository, AppConfig(database_url="postgresql://test"))

    with pytest.raises(ServiceError) as exc_info:
        service.login("admin", "bad-password", ip_address="127.0.0.1")

    assert exc_info.value.status_code == 401
    assert repository.audit_events[-1]["event_type"] == "auth.login_failed"

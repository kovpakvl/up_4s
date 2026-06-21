import pytest

from datetime import UTC, datetime, timedelta

from secureoffice_backend.config import AppConfig
from secureoffice_backend.security import hash_password
from secureoffice_backend.services import (
    AuthService,
    EmployeeActivationService,
    PasswordEntryService,
    ServiceError,
    SetupService,
)


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

    def create_employee_user(self, username, display_name, password_hash, salt, employee_id):
        user = {
            "id": len(self.users) + 1,
            "username": username,
            "display_name": display_name,
            "password_hash": password_hash,
            "salt": salt,
            "access_role": "employee",
            "employee_id": employee_id,
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


class FakeEmployeeRepository:
    def __init__(self):
        self.employees = {}
        self.keys = {}
        self.used_keys = set()
        self.employee_users = set()

    def create_employee(self, full_name, email="", phone=""):
        employee = {
            "id": len(self.employees) + 1,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "status": "active",
        }
        self.employees[employee["id"]] = employee
        return employee

    def list_employees(self):
        return list(self.employees.values())

    def employee_has_user(self, employee_id):
        return employee_id in self.employee_users

    def employee_exists(self, employee_id):
        return employee_id in self.employees

    def create_activation_key(self, employee_id, code_hash, expires_at, created_by):
        key = {
            "id": len(self.keys) + 1,
            "employee_id": employee_id,
            "code_hash": code_hash,
            "expires_at": expires_at,
            "used_at": None,
            "full_name": self.employees[employee_id]["full_name"],
            "email": self.employees[employee_id]["email"],
        }
        self.keys[code_hash] = key
        return key

    def find_activation_key(self, code_hash):
        return self.keys.get(code_hash)

    def mark_activation_key_used(self, key_id):
        for key in self.keys.values():
            if key["id"] == key_id:
                key["used_at"] = datetime.now(UTC)
                self.employee_users.add(key["employee_id"])


def test_activation_service_creates_employee_key_and_user():
    auth_repository = FakeAuthRepository()
    admin = auth_repository.create_admin("admin", "Admin", "hash", "salt")
    employee_repository = FakeEmployeeRepository()
    service = EmployeeActivationService(
        employee_repository,
        auth_repository,
        AppConfig(database_url="postgresql://test"),
    )

    employee = service.create_employee(admin, "Olena User", "u@example.test")
    key = service.create_activation_key(admin, employee["id"])
    user = service.activate(key["code"], "olena", "StrongPass123!")

    assert user["access_role"] == "employee"
    assert user["employee_id"] == employee["id"]
    assert employee_repository.employee_has_user(employee["id"])


def test_activation_service_lists_employees_for_admin():
    auth_repository = FakeAuthRepository()
    admin = auth_repository.create_admin("admin", "Admin", "hash", "salt")
    employee_repository = FakeEmployeeRepository()
    service = EmployeeActivationService(
        employee_repository,
        auth_repository,
        AppConfig(database_url="postgresql://test"),
    )
    service.create_employee(admin, "First User")
    service.create_employee(admin, "Second User")

    employees = service.list_employees(admin)

    assert [employee["full_name"] for employee in employees] == [
        "First User",
        "Second User",
    ]


def test_activation_service_rejects_missing_employee():
    auth_repository = FakeAuthRepository()
    admin = auth_repository.create_admin("admin", "Admin", "hash", "salt")
    service = EmployeeActivationService(
        FakeEmployeeRepository(),
        auth_repository,
        AppConfig(database_url="postgresql://test"),
    )

    with pytest.raises(ServiceError) as exc_info:
        service.create_activation_key(admin, 404)

    assert exc_info.value.status_code == 404


class FakePasswordRepository:
    def __init__(self):
        self.entries = {}
        self.history = []

    def list_entries(self, employee_id):
        return [
            entry
            for entry in self.entries.values()
            if entry["employee_id"] == employee_id
        ]

    def get_entry(self, employee_id, entry_id):
        entry = self.entries.get(entry_id)
        if entry and entry["employee_id"] == employee_id:
            return entry
        return None

    def create_entry(
        self,
        employee_id,
        service_name,
        site_url,
        login,
        encrypted_password,
        comment,
        is_favorite,
        created_by,
    ):
        entry = {
            "id": len(self.entries) + 1,
            "employee_id": employee_id,
            "service_name": service_name,
            "site_url": site_url,
            "login": login,
            "encrypted_password": encrypted_password,
            "comment": comment,
            "is_favorite": is_favorite,
            "password_changed_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        self.entries[entry["id"]] = entry
        return entry

    def update_entry(
        self,
        employee_id,
        entry_id,
        service_name,
        site_url,
        login,
        encrypted_password,
        comment,
        is_favorite,
        password_changed,
    ):
        entry = self.get_entry(employee_id, entry_id)
        if entry is None:
            return None
        entry.update(
            service_name=service_name,
            site_url=site_url,
            login=login,
            encrypted_password=encrypted_password,
            comment=comment,
            is_favorite=is_favorite,
            updated_at=datetime.now(UTC),
        )
        return entry

    def delete_entry(self, employee_id, entry_id):
        if self.get_entry(employee_id, entry_id) is None:
            return False
        del self.entries[entry_id]
        return True

    def add_history(self, entry_id, encrypted_password, changed_by):
        self.history.append(
            {
                "id": len(self.history) + 1,
                "entry_id": entry_id,
                "encrypted_password": encrypted_password,
                "changed_by_name": "User",
                "created_at": datetime.now(UTC),
            }
        )

    def list_history(self, employee_id, entry_id):
        return [row for row in self.history if row["entry_id"] == entry_id]


class FakeCipher:
    def encrypt(self, value):
        return f"encrypted:{value}"

    def decrypt(self, token):
        return token.removeprefix("encrypted:")


def test_password_entry_service_manages_employee_entries():
    auth_repository = FakeAuthRepository()
    password_repository = FakePasswordRepository()
    service = PasswordEntryService(password_repository, auth_repository, FakeCipher())
    user = {
        "id": 7,
        "access_role": "employee",
        "employee_id": 3,
        "display_name": "Olena User",
    }

    entry = service.create_entry(
        user,
        {
            "service_name": "Mail",
            "site_url": "https://mail.example.test",
            "login": "olena",
            "password": "StrongPass123!",
        },
    )
    updated = service.update_entry(
        user,
        entry["id"],
        {
            "service_name": "Mail",
            "site_url": "https://mail.example.test",
            "login": "olena",
            "password": "NewStrongPass123!",
        },
    )

    assert service.list_entries(user)[0]["password"] == "NewStrongPass123!"
    assert updated["password"] == "NewStrongPass123!"
    assert len(service.list_history(user, entry["id"])) == 2
    service.delete_entry(user, entry["id"])
    assert service.list_entries(user) == []

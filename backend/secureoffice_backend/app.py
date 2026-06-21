from flask import Flask

from .config import AppConfig
from .crypto import PasswordCipher
from .db import Database
from .repositories import (
    AuditRepository,
    AuthRepository,
    EmployeeRepository,
    PasswordEntryRepository,
)
from .routes import register_routes
from .services import (
    AuthService,
    AdminPasswordEntryService,
    AuditService,
    EmployeeActivationService,
    PasswordEntryService,
    ProfileService,
    SetupService,
)


def create_app(
    config: AppConfig | None = None,
    database: Database | None = None,
) -> Flask:
    config = config or AppConfig.from_env()
    database = database or Database(config.database_url)

    app = Flask(__name__)
    app.secret_key = config.secret_key
    app.config["SECUREOFFICE_CONFIG"] = config
    app.extensions["secureoffice_database"] = database

    auth_repository = AuthRepository(database)
    employee_repository = EmployeeRepository(database)
    password_repository = PasswordEntryRepository(database)
    audit_repository = AuditRepository(database)
    cipher = PasswordCipher(config.fernet_key)

    setup_service = SetupService(auth_repository)
    auth_service = AuthService(auth_repository, config)
    activation_service = EmployeeActivationService(
        employee_repository,
        auth_repository,
        config,
    )
    password_service = PasswordEntryService(password_repository, auth_repository, cipher)
    admin_password_service = AdminPasswordEntryService(
        password_repository,
        auth_repository,
        cipher,
    )
    audit_service = AuditService(audit_repository)
    profile_service = ProfileService(auth_repository, employee_repository)
    register_routes(
        app,
        setup_service,
        auth_service,
        activation_service,
        password_service,
        admin_password_service,
        audit_service,
        profile_service,
    )

    return app

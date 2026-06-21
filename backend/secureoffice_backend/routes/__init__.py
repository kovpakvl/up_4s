from flask import Flask

from ..services import (
    AuthService,
    AdminPasswordEntryService,
    AuditService,
    EmployeeActivationService,
    PasswordEntryService,
    ProfileService,
    SetupService,
)
from .admin import register_admin_routes
from .auth import register_auth_routes
from .health import register_health_routes
from .profile import register_profile_routes
from .web import register_web_routes


def register_routes(
    app: Flask,
    setup_service: SetupService,
    auth_service: AuthService,
    activation_service: EmployeeActivationService,
    password_service: PasswordEntryService,
    admin_password_service: AdminPasswordEntryService,
    audit_service: AuditService,
    profile_service: ProfileService,
) -> None:
    register_health_routes(app, setup_service)
    register_auth_routes(app, setup_service, auth_service)
    register_admin_routes(
        app,
        auth_service,
        activation_service,
        admin_password_service,
        audit_service,
    )
    register_profile_routes(app, auth_service, profile_service)
    register_web_routes(
        app,
        auth_service,
        activation_service,
        password_service,
        profile_service,
    )

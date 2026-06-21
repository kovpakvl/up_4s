from flask import Flask

from ..services import AuthService, SetupService
from .auth import register_auth_routes
from .health import register_health_routes


def register_routes(
    app: Flask,
    setup_service: SetupService,
    auth_service: AuthService,
) -> None:
    register_health_routes(app, setup_service)
    register_auth_routes(app, setup_service, auth_service)

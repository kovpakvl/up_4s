from flask import Flask

from .config import AppConfig
from .db import Database
from .repositories import AuthRepository
from .routes import register_routes
from .services import AuthService, SetupService


def create_app(
    config: AppConfig | None = None,
    database: Database | None = None,
) -> Flask:
    config = config or AppConfig.from_env()
    database = database or Database(config.database_url)

    app = Flask(__name__)
    app.config["SECUREOFFICE_CONFIG"] = config
    app.extensions["secureoffice_database"] = database

    auth_repository = AuthRepository(database)
    setup_service = SetupService(auth_repository)
    auth_service = AuthService(auth_repository, config)
    register_routes(app, setup_service, auth_service)

    return app

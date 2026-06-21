from flask import Flask, jsonify

from ..services import SetupService


def register_health_routes(app: Flask, setup_service: SetupService) -> None:
    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/status")
    def status():
        return jsonify(setup_service.status())

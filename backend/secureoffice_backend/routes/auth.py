from flask import Flask, jsonify, request

from ..services import AuthService, ServiceError, SetupService


def register_auth_routes(
    app: Flask,
    setup_service: SetupService,
    auth_service: AuthService,
) -> None:
    @app.post("/api/setup-admin")
    def setup_admin():
        data = request.get_json(silent=True) or {}
        try:
            user = setup_service.create_admin(
                username=str(data.get("username", "")),
                display_name=str(data.get("display_name") or data.get("full_name") or ""),
                password=str(data.get("password", "")),
            )
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(user=user), 201

    @app.post("/api/login")
    def login():
        data = request.get_json(silent=True) or {}
        try:
            payload = auth_service.login(
                username=str(data.get("username", "")),
                password=str(data.get("password", "")),
                ip_address=request.remote_addr or "",
            )
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(payload)

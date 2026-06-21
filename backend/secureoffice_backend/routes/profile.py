"""HTTP-эндпоинты профиля текущего пользователя."""
from __future__ import annotations

from functools import wraps

from flask import Flask, jsonify, request

from ..services import AuthService, ProfileService, ServiceError


def register_profile_routes(
    app: Flask,
    auth_service: AuthService,
    profile_service: ProfileService,
) -> None:
    def login_required(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            token = header.removeprefix("Bearer ").strip()
            user = auth_service.user_from_token(token)
            if not user:
                return jsonify(error="Нужна авторизация."), 401
            request.current_user = user
            return view(*args, **kwargs)

        return wrapper

    @app.get("/api/me")
    @login_required
    def get_profile():
        try:
            payload = profile_service.me(request.current_user)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(payload)

    @app.put("/api/me")
    @login_required
    def update_profile():
        data = request.get_json(silent=True) or {}
        try:
            payload = profile_service.update(
                request.current_user,
                display_name=data.get("display_name"),
                email=data.get("email"),
                phone=data.get("phone"),
            )
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(payload)

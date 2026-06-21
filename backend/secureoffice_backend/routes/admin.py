from functools import wraps

from flask import Flask, jsonify, request

from ..services import AuthService, EmployeeActivationService, ServiceError


def register_admin_routes(
    app: Flask,
    auth_service: AuthService,
    activation_service: EmployeeActivationService,
) -> None:
    def admin_required(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            token = header.removeprefix("Bearer ").strip()
            user = auth_service.user_from_token(token)
            if not user or user.get("access_role") != "admin":
                return jsonify(error="Недостаточно прав."), 403
            request.current_user = user
            return view(*args, **kwargs)

        return wrapper

    @app.post("/api/admin/employees")
    @admin_required
    def create_employee():
        data = request.get_json(silent=True) or {}
        try:
            employee = activation_service.create_employee(
                actor_user=request.current_user,
                full_name=str(data.get("full_name", "")),
                email=str(data.get("email", "")),
                phone=str(data.get("phone", "")),
            )
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(employee), 201

    @app.get("/api/admin/employees")
    @admin_required
    def list_employees():
        try:
            employees = activation_service.list_employees(request.current_user)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(employees)

    @app.post("/api/admin/employees/<int:employee_id>/activation-key")
    @admin_required
    def create_activation_key(employee_id: int):
        try:
            payload = activation_service.create_activation_key(
                request.current_user,
                employee_id,
            )
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(payload), 201

from functools import wraps

from flask import Flask, jsonify, request

from ..services import (
    AdminPasswordEntryService,
    AuditService,
    AuthService,
    EmployeeActivationService,
    ServiceError,
)


def register_admin_routes(
    app: Flask,
    auth_service: AuthService,
    activation_service: EmployeeActivationService,
    password_service: AdminPasswordEntryService,
    audit_service: AuditService,
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

    @app.get("/api/admin/password-entries")
    @admin_required
    def list_password_entries():
        try:
            entries = password_service.list_entries(request.current_user)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(entries)

    @app.post("/api/admin/password-entries")
    @admin_required
    def create_password_entries():
        data = request.get_json(silent=True) or {}
        try:
            entries = password_service.create_entries(request.current_user, data)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(entries), 201

    @app.get("/api/admin/password-entries/<int:entry_id>")
    @admin_required
    def get_password_entry(entry_id: int):
        try:
            entry = password_service.get_entry(request.current_user, entry_id)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(entry)

    @app.put("/api/admin/password-entries/<int:entry_id>")
    @admin_required
    def update_password_entry(entry_id: int):
        data = request.get_json(silent=True) or {}
        try:
            entry = password_service.update_entry(request.current_user, entry_id, data)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(entry)

    @app.delete("/api/admin/password-entries/<int:entry_id>")
    @admin_required
    def delete_password_entry(entry_id: int):
        try:
            password_service.delete_entry(request.current_user, entry_id)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(message="Запись удалена.")

    @app.get("/api/admin/password-entries/<int:entry_id>/history")
    @admin_required
    def password_entry_history(entry_id: int):
        try:
            history = password_service.list_history(request.current_user, entry_id)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(history)

    @app.get("/api/admin/audit-events")
    @admin_required
    def audit_events():
        limit = request.args.get("limit", default=200, type=int)
        try:
            events = audit_service.list_events(request.current_user, limit)
        except ServiceError as exc:
            return jsonify(error=str(exc)), exc.status_code
        return jsonify(events)

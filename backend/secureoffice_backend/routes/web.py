from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from ..services import (
    AuthService,
    EmployeeActivationService,
    PasswordEntryService,
    ProfileService,
    ServiceError,
)


def register_web_routes(
    app: Flask,
    auth_service: AuthService,
    activation_service: EmployeeActivationService,
    password_service: PasswordEntryService,
    profile_service: ProfileService,
) -> None:
    def current_user():
        return auth_service.user_from_id(session.get("user_id"))

    def employee_required(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("web_login"))
            if user["access_role"] != "employee":
                flash("Веб-кабинет доступен сотрудникам.", "error")
                return redirect(url_for("web_login"))
            return view(user, *args, **kwargs)

        return wrapper

    @app.get("/")
    def web_index():
        return redirect(url_for("cabinet"))

    @app.route("/activate", methods=["GET", "POST"])
    def activate():
        if request.method == "POST":
            password = request.form.get("password", "")
            repeat_password = request.form.get("repeat_password", "")
            if password != repeat_password:
                flash("Пароли не совпадают.", "error")
                return render_template("activate.html")
            try:
                user = activation_service.activate(
                    code=request.form.get("code", ""),
                    username=request.form.get("username", ""),
                    password=password,
                )
            except ServiceError as exc:
                flash(str(exc), "error")
                return render_template("activate.html")
            session["user_id"] = user["id"]
            flash("Учётная запись активирована.", "success")
            return redirect(url_for("cabinet"))
        return render_template("activate.html")

    @app.route("/login", methods=["GET", "POST"])
    def web_login():
        if request.method == "POST":
            try:
                payload = auth_service.login(
                    username=request.form.get("username", ""),
                    password=request.form.get("password", ""),
                    ip_address=request.remote_addr or "",
                )
            except ServiceError as exc:
                flash(str(exc), "error")
                return render_template("login.html")
            user = payload["user"]
            if user["access_role"] != "employee":
                flash("Войдите через админское приложение.", "error")
                return render_template("login.html")
            session["user_id"] = user["id"]
            return redirect(url_for("cabinet"))
        return render_template("login.html")

    @app.post("/logout")
    def web_logout():
        session.clear()
        return redirect(url_for("web_login"))

    @app.get("/cabinet")
    @employee_required
    def cabinet(user):
        entries = password_service.list_entries(user)
        return render_template("cabinet.html", user=user, entries=entries)

    @app.route("/cabinet/entries/new", methods=["GET", "POST"])
    @employee_required
    def new_entry(user):
        if request.method == "POST":
            try:
                password_service.create_entry(user, _entry_form_data())
            except ServiceError as exc:
                flash(str(exc), "error")
                return render_template("entry_form.html", user=user, entry=None)
            flash("Запись сохранена.", "success")
            return redirect(url_for("cabinet"))
        return render_template("entry_form.html", user=user, entry=None)

    @app.route("/cabinet/entries/<int:entry_id>/edit", methods=["GET", "POST"])
    @employee_required
    def edit_entry(user, entry_id: int):
        try:
            entry = password_service.get_entry(user, entry_id)
        except ServiceError as exc:
            flash(str(exc), "error")
            return redirect(url_for("cabinet"))
        if request.method == "POST":
            try:
                password_service.update_entry(user, entry_id, _entry_form_data())
            except ServiceError as exc:
                flash(str(exc), "error")
                return render_template(
                    "entry_form.html",
                    user=user,
                    entry={**entry, **_entry_form_data()},
                )
            flash("Запись обновлена.", "success")
            return redirect(url_for("cabinet"))
        return render_template("entry_form.html", user=user, entry=entry)

    @app.post("/cabinet/entries/<int:entry_id>/delete")
    @employee_required
    def delete_entry(user, entry_id: int):
        try:
            password_service.delete_entry(user, entry_id)
        except ServiceError as exc:
            flash(str(exc), "error")
        else:
            flash("Запись удалена.", "success")
        return redirect(url_for("cabinet"))

    @app.route("/profile", methods=["GET", "POST"])
    @employee_required
    def profile(user):
        if request.method == "POST":
            try:
                profile = profile_service.update(
                    user,
                    display_name=request.form.get("display_name"),
                    email=request.form.get("email"),
                    phone=request.form.get("phone"),
                )
            except ServiceError as exc:
                flash(str(exc), "error")
                return render_template(
                    "profile.html",
                    user=user,
                    profile=profile_service.me(user),
                )
            flash("Профиль обновлён.", "success")
            session["user_id"] = profile["id"]
            return redirect(url_for("profile"))
        return render_template(
            "profile.html",
            user=user,
            profile=profile_service.me(user),
        )

    @app.get("/cabinet/entries/<int:entry_id>/history")
    @employee_required
    def entry_history(user, entry_id: int):
        try:
            entry = password_service.get_entry(user, entry_id)
            history = password_service.list_history(user, entry_id)
        except ServiceError as exc:
            flash(str(exc), "error")
            return redirect(url_for("cabinet"))
        return render_template("history.html", user=user, entry=entry, history=history)


def _entry_form_data() -> dict:
    return {
        "service_name": request.form.get("service_name", ""),
        "site_url": request.form.get("site_url", ""),
        "login": request.form.get("login", ""),
        "password": request.form.get("password", ""),
        "comment": request.form.get("comment", ""),
        "is_favorite": bool(request.form.get("is_favorite")),
    }

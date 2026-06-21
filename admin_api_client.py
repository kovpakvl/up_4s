import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class AdminApiError(RuntimeError):
    pass


class AdminApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = ""
        self.user: dict = {}

    def request(self, method: str, path: str, data=None, params=None, auth=True):
        url = f"{self.base_url}{path}"
        if params:
            clean = {key: value for key, value in params.items() if value not in (None, "")}
            if clean:
                url = f"{url}?{urlencode(clean)}"
        headers = {"Content-Type": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read()
                return json.loads(payload.decode("utf-8")) if payload else {}
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
                message = payload.get("error", str(exc))
            except (ValueError, UnicodeDecodeError):
                message = str(exc)
            raise AdminApiError(message) from exc
        except (URLError, TimeoutError) as exc:
            raise AdminApiError("Сервер SecureOffice недоступен.") from exc

    def health(self):
        return self.request("GET", "/health", auth=False)

    def status(self):
        return self.request("GET", "/api/status", auth=False)

    def setup_admin(self, username: str, display_name: str, password: str):
        return self.request(
            "POST",
            "/api/setup-admin",
            {"username": username, "display_name": display_name, "password": password},
            auth=False,
        )

    def login(self, username: str, password: str):
        payload = self.request(
            "POST",
            "/api/login",
            {"username": username, "password": password},
            auth=False,
        )
        user = payload["user"]
        if user.get("access_role") != "admin":
            raise AdminApiError("В админское приложение может войти только администратор.")
        self.token = payload["token"]
        self.user = user
        return user

    def employees(self):
        return self.request("GET", "/api/admin/employees")

    def create_employee(self, full_name: str, email: str, phone: str):
        return self.request(
            "POST",
            "/api/admin/employees",
            {"full_name": full_name, "email": email, "phone": phone},
        )

    def create_activation_key(self, employee_id: int):
        return self.request(
            "POST",
            f"/api/admin/employees/{employee_id}/activation-key",
        )

import json
from dataclasses import asdict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class CompanyApiError(RuntimeError):
    pass


class CompanyClient:
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
            raise CompanyApiError(message) from exc
        except (URLError, TimeoutError) as exc:
            raise CompanyApiError(
                "Не удалось подключиться к серверу компании. Проверьте адрес и запуск сервера."
            ) from exc

    def status(self):
        return self.request("GET", "/api/status", auth=False)

    def setup_admin(self, username: str, password: str, full_name: str):
        return self.request(
            "POST",
            "/api/setup-admin",
            {"username": username, "password": password, "full_name": full_name},
            auth=False,
        )

    def register(self, invite_code: str, username: str, password: str, full_name: str, phone: str):
        return self.request(
            "POST",
            "/api/register",
            {
                "invite_code": invite_code,
                "username": username,
                "password": password,
                "full_name": full_name,
                "phone": phone,
            },
            auth=False,
        )

    def login(self, username: str, password: str):
        payload = self.request(
            "POST",
            "/api/login",
            {"username": username, "password": password},
            auth=False,
        )
        self.token = payload["token"]
        self.user = payload["user"]
        return self.user

    def logout(self):
        if self.token:
            try:
                self.request("POST", "/api/logout")
            finally:
                self.token = ""
                self.user = {}

    def departments(self):
        return self.request("GET", "/api/departments")

    def service_types(self):
        return self.request("GET", "/api/service-types")

    def create_invitation(self, email: str, department_id: int, employee_role: str):
        return self.request(
            "POST",
            "/api/invitations",
            {
                "email": email,
                "department_id": department_id,
                "employee_role": employee_role,
            },
        )

    def create_backup(self):
        return self.request("POST", "/api/backup")


class CompanyEmployeeService:
    def __init__(self, client: CompanyClient):
        self.client = client

    def list_employees(self, query: str = "", department_id=None):
        return self.client.request(
            "GET",
            "/api/employees",
            params={"q": query, "department_id": department_id},
        )

    def get_employee(self, employee_id: int):
        return self.client.request("GET", f"/api/employees/{employee_id}")

    def add_employee(self, employee):
        payload = self.client.request("POST", "/api/employees", asdict(employee))
        return int(payload["id"])

    def update_employee(self, employee):
        self.client.request("PUT", f"/api/employees/{employee.id}", asdict(employee))

    def delete_employee(self, employee_id: int):
        self.client.request("DELETE", f"/api/employees/{employee_id}")
        return True


class CompanyAccountService:
    def __init__(self, client: CompanyClient):
        self.client = client

    def dashboard_stats(self):
        return self.client.request("GET", "/api/stats")

    def list_accounts(self, employee_id=None, query: str = "", department_id=None):
        return self.client.request(
            "GET",
            "/api/accounts",
            params={
                "employee_id": employee_id,
                "q": query,
                "department_id": department_id,
            },
        )

    def get_account(self, account_id: int):
        return self.client.request("GET", f"/api/accounts/{account_id}")

    def add_account(self, account):
        payload = self.client.request("POST", "/api/accounts", asdict(account))
        return int(payload["id"])

    def update_account(self, account, password_changed: bool):
        payload = asdict(account)
        payload["password_changed"] = password_changed
        self.client.request("PUT", f"/api/accounts/{account.id}", payload)

    def delete_account(self, account_id: int):
        self.client.request("DELETE", f"/api/accounts/{account_id}")

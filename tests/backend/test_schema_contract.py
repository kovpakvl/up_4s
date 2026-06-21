from pathlib import Path


SCHEMA = Path("backend/secureoffice_backend/schema.sql")


def test_schema_contains_core_tables():
    schema = SCHEMA.read_text(encoding="utf-8")

    for table in [
        "departments",
        "positions",
        "employees",
        "users",
        "activation_keys",
        "sessions",
        "password_entries",
        "password_history",
        "audit_events",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema


def test_schema_keeps_employee_password_entries_one_owner():
    schema = SCHEMA.read_text(encoding="utf-8")

    assert "employee_id BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE" in schema

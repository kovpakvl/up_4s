from contextlib import contextmanager
from pathlib import Path
from time import sleep
from typing import Iterator


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    @contextmanager
    def connection(self):
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            yield conn

    def initialize(self) -> None:
        with self.connection() as conn:
            for statement in read_schema_statements():
                conn.execute(statement)
            conn.commit()

    def wait_until_ready(self, attempts: int = 20, delay_seconds: float = 1.0) -> None:
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                with self.connection() as conn:
                    conn.execute("SELECT 1")
                return
            except Exception as exc:  # pragma: no cover - depends on Docker timing
                last_error = exc
                sleep(delay_seconds)
        raise RuntimeError("Database is not available.") from last_error


def read_schema_statements() -> Iterator[str]:
    # Used by tests and small maintenance scripts.
    for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
        statement = statement.strip()
        if statement:
            yield statement

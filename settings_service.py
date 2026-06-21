import sqlite3
from contextlib import closing
from datetime import datetime

from config import AUTO_LOCK_MINUTES, BACKUP_DIR, CLIPBOARD_CLEAR_SECONDS, DB_PATH
from database import get_connection


DEFAULT_SETTINGS = {
    "hide_passwords": "1",
    "clipboard_clear_seconds": str(CLIPBOARD_CLEAR_SECONDS),
    "auto_lock_minutes": str(AUTO_LOCK_MINUTES),
    "default_password_length": "16",
    "theme": "light",
}


class SettingsService:
    def ensure_defaults(self) -> None:
        with get_connection() as conn:
            for name, value in DEFAULT_SETTINGS.items():
                conn.execute(
                    """
                    INSERT OR IGNORE INTO settings (setting_name, setting_value)
                    VALUES (?, ?)
                    """,
                    (name, value),
                )
            conn.commit()

    def get(self, name: str, default: str = "") -> str:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT setting_value FROM settings WHERE setting_name = ?", (name,)
            ).fetchone()
        return row["setting_value"] if row else default

    def set(self, name: str, value: str) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (setting_name, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_name)
                DO UPDATE SET setting_value = excluded.setting_value
                """,
                (name, value),
            )
            conn.commit()

    def all(self) -> dict[str, str]:
        with get_connection() as conn:
            rows = conn.execute("SELECT setting_name, setting_value FROM settings").fetchall()
        values = DEFAULT_SETTINGS.copy()
        values.update({row["setting_name"]: row["setting_value"] for row in rows})
        return values

    def create_backup(self) -> str:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        target = BACKUP_DIR / f"backup_{timestamp}.db"
        with closing(sqlite3.connect(DB_PATH)) as source, closing(
            sqlite3.connect(target)
        ) as backup:
            source.backup(backup)
        return str(target)

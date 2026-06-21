from dataclasses import dataclass
from typing import Optional

from crypto_service import CryptoService
from database import get_connection


@dataclass
class PasswordEntry:
    id: Optional[int]
    service_name: str
    site_url: str
    login: str
    password: str
    email: str
    comment: str
    category: str
    is_favorite: bool = False


class PasswordService:
    def __init__(self, crypto: CryptoService):
        self.crypto = crypto

    def list_entries(self, query: str = "") -> list[dict]:
        query = query.strip()
        with get_connection() as conn:
            if query:
                like = f"%{query}%"
                rows = conn.execute(
                    """
                    SELECT id, service_name, site_url, login, email, category,
                           is_favorite, created_at, updated_at
                    FROM password_entries
                    WHERE service_name LIKE ?
                       OR site_url LIKE ?
                       OR login LIKE ?
                       OR email LIKE ?
                       OR category LIKE ?
                    ORDER BY is_favorite DESC, updated_at DESC, service_name COLLATE NOCASE
                    """,
                    (like, like, like, like, like),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, service_name, site_url, login, email, category,
                           is_favorite, created_at, updated_at
                    FROM password_entries
                    ORDER BY is_favorite DESC, updated_at DESC, service_name COLLATE NOCASE
                    """
                ).fetchall()
        return [dict(row) for row in rows]

    def get_entry(self, entry_id: int) -> Optional[PasswordEntry]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM password_entries WHERE id = ?", (entry_id,)
            ).fetchone()
        if row is None:
            return None
        return PasswordEntry(
            id=row["id"],
            service_name=row["service_name"],
            site_url=row["site_url"],
            login=row["login"],
            password=self.crypto.decrypt(row["encrypted_password"]),
            email=row["email"],
            comment=row["comment"],
            category=row["category"],
            is_favorite=bool(row["is_favorite"]),
        )

    def add_entry(self, entry: PasswordEntry) -> int:
        encrypted_password = self.crypto.encrypt(entry.password)
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO password_entries (
                    service_name, site_url, login, encrypted_password, email,
                    comment, category, is_favorite
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.service_name,
                    entry.site_url,
                    entry.login,
                    encrypted_password,
                    entry.email,
                    entry.comment,
                    entry.category,
                    int(entry.is_favorite),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def update_entry(self, entry: PasswordEntry) -> None:
        if entry.id is None:
            raise ValueError("Нельзя обновить запись без id.")
        encrypted_password = self.crypto.encrypt(entry.password)
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE password_entries
                SET service_name = ?,
                    site_url = ?,
                    login = ?,
                    encrypted_password = ?,
                    email = ?,
                    comment = ?,
                    category = ?,
                    is_favorite = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    entry.service_name,
                    entry.site_url,
                    entry.login,
                    encrypted_password,
                    entry.email,
                    entry.comment,
                    entry.category,
                    int(entry.is_favorite),
                    entry.id,
                ),
            )
            conn.commit()

    def delete_entry(self, entry_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM password_entries WHERE id = ?", (entry_id,))
            conn.commit()

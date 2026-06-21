import base64
import hashlib
import hmac
import os
from typing import Optional

from config import PBKDF2_ITERATIONS
from database import get_connection


def _hash_password(master_password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return base64.b64encode(digest).decode("ascii")


def validate_new_master_password(password: str, repeat_password: str) -> tuple[bool, str]:
    if not password:
        return False, "Мастер-пароль не должен быть пустым."
    if len(password) < 10:
        return False, "Мастер-пароль должен быть не короче 10 символов."
    checks = [
        any(ch.islower() for ch in password),
        any(ch.isupper() for ch in password),
        any(ch.isdigit() for ch in password),
        any(not ch.isalnum() for ch in password),
    ]
    if sum(checks) < 3:
        return False, (
            "Используйте минимум три типа символов: строчные и заглавные буквы, "
            "цифры или специальные знаки."
        )
    if password != repeat_password:
        return False, "Пароли не совпадают."
    return True, ""


def create_user(master_password: str) -> bytes:
    salt = os.urandom(16)
    password_hash = _hash_password(master_password, salt)
    with get_connection() as conn:
        conn.execute("DELETE FROM users")
        conn.execute(
            "INSERT INTO users (id, master_password_hash, salt) VALUES (1, ?, ?)",
            (password_hash, base64.b64encode(salt).decode("ascii")),
        )
        conn.commit()
    return salt


def get_user_salt() -> Optional[bytes]:
    with get_connection() as conn:
        row = conn.execute("SELECT salt FROM users WHERE id = 1").fetchone()
    if row is None:
        return None
    return base64.b64decode(row["salt"])


def verify_master_password(master_password: str) -> Optional[bytes]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT master_password_hash, salt FROM users WHERE id = 1"
        ).fetchone()
    if row is None:
        return None

    salt = base64.b64decode(row["salt"])
    candidate_hash = _hash_password(master_password, salt)
    if hmac.compare_digest(candidate_hash, row["master_password_hash"]):
        return salt
    return None

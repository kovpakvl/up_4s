import base64
import hashlib

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as exc:  # pragma: no cover - shown in UI at runtime
    raise RuntimeError(
        "Не установлена библиотека cryptography. Выполните: pip install -r requirements.txt"
    ) from exc

from config import PBKDF2_ITERATIONS


def derive_key(master_password: str, salt: bytes) -> bytes:
    raw_key = hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    return base64.urlsafe_b64encode(raw_key)


class CryptoService:
    def __init__(self, master_password: str, salt: bytes):
        self._fernet = Fernet(derive_key(master_password, salt))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Не удалось расшифровать пароль") from exc

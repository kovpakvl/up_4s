class PasswordCipher:
    def __init__(self, fernet_key: str):
        from cryptography.fernet import Fernet, InvalidToken

        self._fernet = Fernet(fernet_key.encode("ascii"))
        self._invalid_token = InvalidToken

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except self._invalid_token as exc:
            raise ValueError("Не удалось расшифровать пароль.") from exc

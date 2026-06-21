import secrets
import string


SIMILAR_SYMBOLS = set("0Ool1I|")
SPECIAL_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/\\"


def generate_password(
    length: int = 16,
    use_digits: bool = True,
    use_lowercase: bool = True,
    use_uppercase: bool = True,
    use_special: bool = True,
    exclude_similar: bool = False,
) -> str:
    pools: list[str] = []
    if use_digits:
        pools.append(string.digits)
    if use_lowercase:
        pools.append(string.ascii_lowercase)
    if use_uppercase:
        pools.append(string.ascii_uppercase)
    if use_special:
        pools.append(SPECIAL_SYMBOLS)

    if not pools:
        raise ValueError("Выберите хотя бы один тип символов.")
    if length < len(pools):
        raise ValueError("Длина меньше количества выбранных типов символов.")

    normalized_pools = []
    for pool in pools:
        if exclude_similar:
            pool = "".join(ch for ch in pool if ch not in SIMILAR_SYMBOLS)
        if not pool:
            raise ValueError("После исключения похожих символов один из наборов пуст.")
        normalized_pools.append(pool)

    password_chars = [secrets.choice(pool) for pool in normalized_pools]
    alphabet = "".join(normalized_pools)
    password_chars.extend(secrets.choice(alphabet) for _ in range(length - len(password_chars)))
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)

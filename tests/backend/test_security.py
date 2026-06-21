from secureoffice_backend.security import (
    generate_token,
    hash_password,
    hash_token,
    validate_password,
    verify_password,
)


def test_password_hash_roundtrip():
    stored_hash, salt = hash_password("StrongPass123!")

    assert verify_password("StrongPass123!", stored_hash, salt)
    assert not verify_password("wrong-password", stored_hash, salt)


def test_password_policy_requires_strength():
    assert validate_password("short")
    assert validate_password("onlylowercase")
    assert validate_password("StrongPass123!") == ""


def test_token_hash_is_stable_and_not_plain_text():
    token = generate_token()

    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token

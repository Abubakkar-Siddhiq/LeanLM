from cryptography.fernet import Fernet, InvalidToken

from config.settings import settings


def _get_cipher() -> Fernet:
    secret = settings.PROVIDER_KEY_ENCRYPTION_SECRET
    if not secret:
        raise ValueError(
            "PROVIDER_KEY_ENCRYPTION_SECRET environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(secret.encode() if isinstance(secret, str) else secret)
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Invalid PROVIDER_KEY_ENCRYPTION_SECRET: {e}. "
            "Generate a valid secret with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )


def encrypt_api_key(raw_key: str) -> str:
    cipher = _get_cipher()
    return cipher.encrypt(raw_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    cipher = _get_cipher()
    try:
        return cipher.decrypt(encrypted_key.encode()).decode()
    except InvalidToken as e:
        raise ValueError(f"Failed to decrypt API key: {e}")

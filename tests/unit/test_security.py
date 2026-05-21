import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import patch

import pytest


VALID_FERNET_KEY = "TVKxptRMdZNkiDKCQGDT3EcETgSyNR4bPrLpusZQynk="


class TestEncryption:
    @patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", VALID_FERNET_KEY)
    def test_encrypt_decrypt_roundtrip(self):
        from core.security import encrypt_api_key, decrypt_api_key

        raw_key = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(raw_key)
        decrypted = decrypt_api_key(encrypted)

        assert decrypted == raw_key

    @patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", VALID_FERNET_KEY)
    def test_encrypted_value_not_equal_to_raw_key(self):
        from core.security import encrypt_api_key

        raw_key = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(raw_key)

        assert encrypted != raw_key

    @patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", "")
    def test_missing_secret_raises_error(self):
        from core.security import encrypt_api_key

        with pytest.raises(ValueError, match="PROVIDER_KEY_ENCRYPTION_SECRET"):
            encrypt_api_key("test-key")

    @patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", "invalid-base64")
    def test_invalid_secret_raises_error(self):
        from core.security import encrypt_api_key

        with pytest.raises(ValueError, match="Invalid PROVIDER_KEY_ENCRYPTION_SECRET"):
            encrypt_api_key("test-key")

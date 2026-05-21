import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import patch

import pytest
from sqlmodel import Session

from api.providers.schemas import ProviderKeyCreate
from api.providers.services import ProviderKeyService
from db.provider_keys import ProviderKey


SERVICE = ProviderKeyService()

ENCRYPT_SECRET = "TVKxptRMdZNkiDKCQGDT3EcETgSyNR4bPrLpusZQynk="


class TestProviderKeyService:
    def test_create_stores_encrypted_not_raw(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            payload = ProviderKeyCreate(provider_name="groq", api_key="sk-raw-groq-key")
            result = SERVICE.create_provider_key(db_session, payload)

        assert result.provider_name == "groq"
        assert result.is_active is True

        stored = db_session.exec(
            __import__("sqlmodel").select(ProviderKey).where(ProviderKey.provider_name == "groq")
        ).first()
        assert stored is not None
        assert stored.encrypted_api_key != "sk-raw-groq-key"
        assert "sk-raw-groq-key" not in stored.encrypted_api_key

    def test_list_keys_does_not_expose_raw_key(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            payload = ProviderKeyCreate(provider_name="openai", api_key="sk-openai-test")
            SERVICE.create_provider_key(db_session, payload)

        keys = SERVICE.list_provider_keys(db_session)
        assert len(keys) == 1
        assert keys[0].provider_name == "openai"
        assert not hasattr(keys[0], "api_key")
        assert not hasattr(keys[0], "encrypted_api_key")

    def test_create_same_provider_updates_existing(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            payload1 = ProviderKeyCreate(provider_name="anthropic", api_key="sk-ant-v1-first")
            result1 = SERVICE.create_provider_key(db_session, payload1)
            first_id = result1.id

            payload2 = ProviderKeyCreate(provider_name="anthropic", api_key="sk-ant-v2-updated")
            result2 = SERVICE.create_provider_key(db_session, payload2)

        assert result2.id == first_id
        assert result2.is_active is True

        count = len(db_session.exec(
            __import__("sqlmodel").select(ProviderKey).where(ProviderKey.provider_name == "anthropic")
        ).all())
        assert count == 1

    def test_delete_disables_provider_key(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            payload = ProviderKeyCreate(provider_name="google", api_key="google-test-key")
            SERVICE.create_provider_key(db_session, payload)

            result = SERVICE.delete_provider_key(db_session, "google")

        assert result is not None
        assert result.provider_name == "google"
        assert result.is_active is False

    def test_validate_returns_false_for_missing_provider(self, db_session: Session):
        result = SERVICE.validate_provider_key(db_session, "nonexistent")

        assert result.valid is False
        assert "no" in result.message.lower() or "not" in result.message.lower()

    def test_validate_returns_true_for_active_stored_provider(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            payload = ProviderKeyCreate(provider_name="groq", api_key="sk-groq-valid")
            SERVICE.create_provider_key(db_session, payload)

        result = SERVICE.validate_provider_key(db_session, "groq")

        assert result.valid is True
        assert result.provider_name == "groq"

    def test_get_available_returns_only_active_providers(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            SERVICE.create_provider_key(db_session, ProviderKeyCreate(provider_name="groq", api_key="g1"))
            SERVICE.create_provider_key(db_session, ProviderKeyCreate(provider_name="openai", api_key="o1"))
            SERVICE.delete_provider_key(db_session, "openai")

        available = SERVICE.get_available_providers(db_session)

        assert "groq" in available
        assert "openai" not in available

    def test_unsupported_provider_is_rejected(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            with pytest.raises(ValueError, match="Unsupported provider"):
                payload = ProviderKeyCreate(provider_name="fake-provider", api_key="some-key")
                SERVICE.create_provider_key(db_session, payload)

    def test_decrypt_returns_raw_key_for_active_provider(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            SERVICE.create_provider_key(db_session, ProviderKeyCreate(provider_name="groq", api_key="sk-secret-groq"))
            decrypted = SERVICE.get_decrypted_api_key(db_session, "groq")
            assert decrypted == "sk-secret-groq"

    def test_decrypt_returns_none_for_missing_provider(self, db_session: Session):
        result = SERVICE.get_decrypted_api_key(db_session, "nonexistent")
        assert result is None

    def test_decrypt_returns_none_for_disabled_provider(self, db_session: Session):
        with patch("config.settings.settings.PROVIDER_KEY_ENCRYPTION_SECRET", ENCRYPT_SECRET):
            SERVICE.create_provider_key(db_session, ProviderKeyCreate(provider_name="openai", api_key="sk-openai"))
            SERVICE.delete_provider_key(db_session, "openai")
            decrypted = SERVICE.get_decrypted_api_key(db_session, "openai")
            assert decrypted is None

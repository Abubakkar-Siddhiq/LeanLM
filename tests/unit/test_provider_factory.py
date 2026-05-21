"""Unit tests for ProviderFactory.available_providers — mocks settings."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import patch

import pytest


class TestProviderFactoryAvailable:
    @patch("config.settings.settings.GROQ_API_KEY", "sk-groq")
    @patch("config.settings.settings.OPENAI_API_KEY", "sk-openai")
    @patch("config.settings.settings.ANTHROPIC_API_KEY", "")
    @patch("config.settings.settings.GEMINI_API_KEY", "")
    def test_returns_only_providers_with_configured_keys(self):
        from providers import ProviderFactory
        available = ProviderFactory.available_providers()
        assert "groq" in available
        assert "openai" in available
        assert "anthropic" not in available
        assert "google" not in available

    def test_unavailable_providers_are_excluded(self):
        from providers import ProviderFactory
        with patch("config.settings.settings.GROQ_API_KEY", ""):
            with patch("config.settings.settings.OPENAI_API_KEY", ""):
                with patch("config.settings.settings.ANTHROPIC_API_KEY", ""):
                    with patch("config.settings.settings.GEMINI_API_KEY", ""):
                        available = ProviderFactory.available_providers()
        assert available == []

    def test_unregistered_provider_not_returned(self):
        from providers import ProviderFactory
        assert "nonexistent" not in ProviderFactory._PROVIDER_KEY_MAP

    @patch("config.settings.settings.GROQ_API_KEY", "sk-groq")
    @patch("config.settings.settings.OPENAI_API_KEY", "sk-openai")
    @patch("config.settings.settings.ALLOW_ENV_PROVIDER_FALLBACK", False)
    def test_returns_empty_when_env_fallback_disabled(self):
        from providers import ProviderFactory
        available = ProviderFactory.available_providers()
        assert available == []

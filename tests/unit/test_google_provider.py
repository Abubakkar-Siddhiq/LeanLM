"""Unit tests for GoogleProvider — mocks genai, no real API calls."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import patch, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


class TestGoogleProvider:
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    async def test_generate_returns_llm_response(self):
        from providers.google import GoogleProvider

        provider = GoogleProvider()
        provider._sync_generate = MagicMock(return_value=MagicMock(
            content="Hello from Gemini",
            provider="google",
            model="gemini-2.0-flash",
            input_tokens=12,
            output_tokens=22,
            total_tokens=34,
            latency_ms=100.0,
            raw=None,
        ))

        from schemas.llm import LLMResponse
        provider._sync_generate.return_value = LLMResponse(
            content="Hello from Gemini",
            provider="google",
            model="gemini-2.0-flash",
            input_tokens=12,
            output_tokens=22,
            total_tokens=34,
            latency_ms=100.0,
            raw=None,
        )

        result = await provider.generate(model="gemini-2.0-flash", messages=[{"role": "user", "content": "Hi"}])

        assert result.content == "Hello from Gemini"
        assert result.provider == "google"
        assert result.model == "gemini-2.0-flash"
        assert result.input_tokens == 12
        assert result.output_tokens == 22
        assert result.total_tokens == 34

    @patch.dict(os.environ, {}, clear=True)
    async def test_generate_raises_without_api_key(self):
        from providers.google import GoogleProvider

        provider = GoogleProvider()
        with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
            await provider.generate(model="gemini-2.0-flash", messages=[])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    async def test_generate_raises_when_env_fallback_disabled(self):
        from providers.google import GoogleProvider

        provider = GoogleProvider()
        with patch("config.settings.settings.ALLOW_ENV_PROVIDER_FALLBACK", False):
            with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
                await provider.generate(model="gemini-2.0-flash", messages=[])

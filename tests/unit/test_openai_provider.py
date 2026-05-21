"""Unit tests for OpenAIProvider — mocks AsyncOpenAI, no real API calls."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


class TestOpenAIProvider:
    @patch("openai.AsyncOpenAI")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    async def test_generate_returns_llm_response(self, mock_async_openai):
        from providers.openai import OpenAIProvider

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Hello from OpenAI"
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 20
        mock_completion.usage.total_tokens = 30
        mock_completion.model_dump.return_value = {"id": "chatcmpl-123"}

        mock_client = AsyncMock()
        mock_async_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        provider = OpenAIProvider()

        result = await provider.generate(model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}])

        assert result.content == "Hello from OpenAI"
        assert result.provider == "openai"
        assert result.model == "gpt-4o-mini"
        assert result.input_tokens == 10
        assert result.output_tokens == 20
        assert result.total_tokens == 30
        assert result.raw["id"] == "chatcmpl-123"

    @patch.dict(os.environ, {}, clear=True)
    async def test_generate_raises_without_api_key(self):
        from providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
            await provider.generate(model="gpt-4o-mini", messages=[])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    async def test_generate_raises_when_env_fallback_disabled(self):
        from providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        with patch("config.settings.settings.ALLOW_ENV_PROVIDER_FALLBACK", False):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
                await provider.generate(model="gpt-4o-mini", messages=[])

    @patch("openai.AsyncOpenAI")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    async def test_byok_key_overrides_env(self, mock_async_openai):
        from providers.openai import OpenAIProvider

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "BYOK reply"
        mock_completion.usage = MagicMock()
        mock_completion.model_dump.return_value = {}

        mock_client = AsyncMock()
        mock_async_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        provider = OpenAIProvider()
        result = await provider.generate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="sk-byok-key"
        )

        assert result.content == "BYOK reply"
        mock_async_openai.assert_called_once_with(api_key="sk-byok-key")

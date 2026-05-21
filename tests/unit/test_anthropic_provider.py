"""Unit tests for AnthropicProvider — mocks AsyncAnthropic, no real API calls."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


class TestAnthropicProvider:
    @patch("anthropic.AsyncAnthropic")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_generate_returns_llm_response(self, mock_async_anthropic):
        from providers.anthropic import AnthropicProvider

        mock_response = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello from Claude"
        mock_response.content = [mock_block]
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        mock_response.model_dump.return_value = {"id": "msg_123"}

        mock_client = AsyncMock()
        mock_async_anthropic.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = AnthropicProvider()

        result = await provider.generate(model="claude-sonnet-4-20250514", messages=[{"role": "user", "content": "Hi"}])

        assert result.content == "Hello from Claude"
        assert result.provider == "anthropic"
        assert result.model == "claude-sonnet-4-20250514"
        assert result.input_tokens == 15
        assert result.output_tokens == 25
        assert result.total_tokens == 40

    @patch.dict(os.environ, {}, clear=True)
    async def test_generate_raises_without_api_key(self):
        from providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
            await provider.generate(model="claude-sonnet-4-20250514", messages=[])

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_generate_raises_when_env_fallback_disabled(self):
        from providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        with patch("config.settings.settings.ALLOW_ENV_PROVIDER_FALLBACK", False):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
                await provider.generate(model="claude-sonnet-4-20250514", messages=[])

    @patch("anthropic.AsyncAnthropic")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_byok_key_overrides_env(self, mock_async_anthropic):
        from providers.anthropic import AnthropicProvider

        mock_response = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "BYOK reply"
        mock_response.content = [mock_block]
        mock_response.usage = MagicMock()
        mock_response.model_dump.return_value = {}

        mock_client = AsyncMock()
        mock_async_anthropic.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = AnthropicProvider()
        result = await provider.generate(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="sk-byok-key"
        )

        assert result.content == "BYOK reply"
        mock_async_anthropic.assert_called_once_with(api_key="sk-byok-key")

"""Unit tests for AnthropicProvider — mocks AsyncAnthropic, no real API calls."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

pytestmark = pytest.mark.asyncio


class TestAnthropicProvider:
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"})
    async def test_generate_returns_llm_response(self):
        from providers.anthropic import AnthropicProvider

        mock_response = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello from Claude"
        mock_response.content = [mock_block]
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        mock_response.model_dump.return_value = {"id": "msg_123"}

        provider = AnthropicProvider()
        provider._client = AsyncMock()
        provider._client.messages.create = AsyncMock(return_value=mock_response)

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

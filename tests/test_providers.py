import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from chronicle.src.providers.base import LLMProvider
from chronicle.src.providers.openai import OpenAIProvider

def test_factory_mapping():
    provider_openai = LLMProvider.get_provider("openai")
    provider_llamacpp = LLMProvider.get_provider("llamacpp")
    assert isinstance(provider_openai, OpenAIProvider)
    assert isinstance(provider_llamacpp, OpenAIProvider)

def test_factory_with_config():
    class DummyConfig:
        openai_base_url = "http://custom-url:9999/v1"
        provider = "openai"
    config = DummyConfig()
    provider = LLMProvider.get_provider("openai", config=config)
    assert provider.base_url == "http://custom-url:9999/v1"

@patch("httpx.Client")
def test_openai_provider_sync_chat(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello response"}}]
    }
    mock_client.post.return_value = mock_response

    provider = OpenAIProvider()
    res = provider.chat("test-model", [{"role": "user", "content": "hello"}])
    assert res == "Hello response"
    mock_client.post.assert_called_once()

@patch("httpx.AsyncClient")
@pytest.mark.asyncio
async def test_openai_provider_async_chat(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello async response"}}]
    }
    mock_client.post = AsyncMock(return_value=mock_response)

    provider = OpenAIProvider()
    res = await provider.chat_async("test-model", [{"role": "user", "content": "hello"}])
    assert res == "Hello async response"
    mock_client.post.assert_called_once()

@patch("httpx.Client")
def test_openai_provider_sync_embed(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [{"embedding": [0.1, 0.2, 0.3]}]
    }
    mock_client.post.return_value = mock_response

    provider = OpenAIProvider()
    res = provider.embed("test text", "test-model")
    assert res == [0.1, 0.2, 0.3]
    mock_client.post.assert_called_once()

@patch("httpx.AsyncClient")
@pytest.mark.asyncio
async def test_openai_provider_async_embed(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [{"embedding": [0.4, 0.5, 0.6]}]
    }
    mock_client.post = AsyncMock(return_value=mock_response)

    provider = OpenAIProvider()
    res = await provider.embed_async("test text", "test-model")
    assert res == [0.4, 0.5, 0.6]
    mock_client.post.assert_called_once()

@patch("httpx.Client")
def test_openai_provider_health_check_pass(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response

    provider = OpenAIProvider()
    assert provider.check_health() is True
    mock_client.get.assert_called_once()

@patch("httpx.Client")
def test_openai_provider_health_check_fail(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    mock_client.get.side_effect = Exception("Connection error")

    provider = OpenAIProvider()
    assert provider.check_health() is False

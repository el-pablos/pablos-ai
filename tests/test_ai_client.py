"""
Unit tests for MegaLLM AI client.
"""

import pytest
from app.ai_client import (
    EndpointConfig, MegaLLMClient, MockMegaLLMClient, 
    create_ai_client, DOAIClient, MockDOAIClient
)


class TestEndpointConfig:
    """Tests for EndpointConfig class."""
    
    def test_endpoint_creation(self):
        """Test creating an endpoint configuration."""
        endpoint = EndpointConfig(
            base_url="https://ai.megallm.io/v1",
            access_key="test-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1",
            name="test-endpoint"
        )
        assert endpoint.base_url == "https://ai.megallm.io/v1"
        assert endpoint.access_key == "test-key"
        assert endpoint.model_chat == "openai-gpt-oss-20b"
        assert endpoint.model_image == "stability-image-1"
        assert endpoint.name == "test-endpoint"
    
    def test_endpoint_is_available_initially(self):
        """Test that endpoint is available initially."""
        endpoint = EndpointConfig(
            base_url="https://ai.megallm.io/v1",
            access_key="test-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1"
        )
        assert endpoint.is_available() is True
    
    def test_endpoint_cooldown(self):
        """Test endpoint cooldown mechanism."""
        endpoint = EndpointConfig(
            base_url="https://ai.megallm.io/v1",
            access_key="test-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1"
        )
        endpoint.mark_rate_limited(cooldown_seconds=1)
        assert endpoint.is_available() is False
        
        # Reset cooldown
        endpoint.reset_cooldown()
        assert endpoint.is_available() is True


class TestMockMegaLLMClient:
    """Tests for MockMegaLLMClient class."""
    
    def test_mock_client_initialization(self):
        """Test mock client initialization."""
        client = MockMegaLLMClient(
            access_key="mock-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1",
            max_tokens=400
        )
        assert client.access_key == "mock-key"
        assert client.model_chat == "openai-gpt-oss-20b"
        assert client.max_tokens == 400
    
    def test_mock_generate_chat_response(self):
        """Test mock chat response generation."""
        client = MockMegaLLMClient(
            access_key="mock-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1"
        )
        response = client.generate_chat_response("Test prompt")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_mock_generate_image(self):
        """Test mock image generation."""
        client = MockMegaLLMClient(
            access_key="mock-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1"
        )
        image_bytes = client.generate_image("Test image prompt")
        assert image_bytes is not None
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0


class TestCreateAIClient:
    """Tests for create_ai_client factory function."""
    
    def test_create_mock_client(self):
        """Test creating mock client."""
        client = create_ai_client(
            access_key="test-key",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1",
            use_mock=True
        )
        assert isinstance(client, MockMegaLLMClient)
    
    def test_create_client_with_endpoints(self):
        """Test creating client with endpoint list."""
        endpoints = [
            EndpointConfig(
                base_url="https://ai.megallm.io/v1",
                access_key="test-key",
                model_chat="openai-gpt-oss-20b",
                model_image="stability-image-1",
                name="primary"
            )
        ]
        client = create_ai_client(endpoints=endpoints)
        assert isinstance(client, MegaLLMClient)
        assert len(client.endpoints) == 1
    
    def test_create_client_legacy_params(self):
        """Test creating client with legacy parameters."""
        client = create_ai_client(
            access_key="test-key",
            base_url="https://ai.megallm.io/v1",
            model_chat="openai-gpt-oss-20b",
            model_image="stability-image-1"
        )
        assert isinstance(client, MegaLLMClient)
        assert len(client.endpoints) == 1
        assert client.endpoints[0].base_url == "https://ai.megallm.io/v1"
    
    def test_backward_compatibility_aliases(self):
        """Test that backward compatibility aliases work."""
        assert DOAIClient is MegaLLMClient
        assert MockDOAIClient is MockMegaLLMClient


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


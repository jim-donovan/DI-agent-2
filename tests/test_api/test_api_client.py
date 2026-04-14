"""Tests for API client and retry logic."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from api_client import APIClient
import time

@pytest.mark.unit
class TestAPIClient:
    """Test APIClient functionality."""

    def test_api_client_initialization(self, mock_config):
        """Test API client initializes correctly."""
        client = APIClient(mock_config)

        assert client.config == mock_config
        # Note: unified_client is on the config object
        assert hasattr(mock_config, 'unified_client')

    def test_successful_api_call(self, mock_config):
        """Test successful API call without retry."""
        # Setup mock unified client on config
        mock_unified = Mock()
        mock_response = Mock()
        mock_response.content = "Success response"
        mock_response.tokens_used = 150
        mock_response.truncated = False
        mock_unified.chat_completion.return_value = mock_response
        mock_config.unified_client = mock_unified

        # Test
        client = APIClient(mock_config)
        messages = [{"role": "user", "content": "Test message"}]
        response, tokens = client.make_api_call(messages, task="main")

        # Verify
        assert response == "Success response"
        assert tokens == 150
        mock_unified.chat_completion.assert_called_once()

    def test_api_call_failure_propagates(self, mock_config):
        """Test API call failures are propagated with context."""
        # Setup mock unified client to fail
        mock_unified = Mock()
        mock_unified.chat_completion.side_effect = Exception("Rate limit error")
        mock_config.unified_client = mock_unified

        # Test
        client = APIClient(mock_config)
        messages = [{"role": "user", "content": "Test"}]

        # Should raise exception with context
        with pytest.raises(Exception, match="API call failed: Rate limit error"):
            client.make_api_call(messages, task="main")

    def test_truncation_detection(self, mock_config):
        """Test truncation detection and logging."""
        mock_unified = Mock()
        mock_response = Mock()
        mock_response.content = "Truncated response"
        mock_response.tokens_used = 100
        mock_response.truncated = True
        mock_unified.chat_completion.return_value = mock_response
        mock_config.unified_client = mock_unified

        client = APIClient(mock_config)
        messages = [{"role": "user", "content": "Test"}]

        response, tokens = client.make_api_call(messages, task="main")

        # Verify truncation was detected
        assert client.last_response_truncated is True
        assert response == "Truncated response"

    def test_api_call_with_different_tasks(self, mock_config):
        """Test API call uses correct config for different tasks."""
        mock_unified = Mock()
        mock_response = Mock()
        mock_response.content = "Response"
        mock_response.tokens_used = 50
        mock_response.truncated = False
        mock_unified.chat_completion.return_value = mock_response
        mock_config.unified_client = mock_unified

        client = APIClient(mock_config)

        # Test vision task
        messages = [{"role": "user", "content": "Test"}]
        client.make_api_call(messages, task="vision")

        # Test main task
        client.make_api_call(messages, task="main")

        # Verify both calls went through
        assert mock_unified.chat_completion.call_count == 2

    def test_task_based_configuration(self, mock_config):
        """Test that task-based configuration is used correctly."""
        mock_unified = Mock()
        mock_response = Mock()
        mock_response.content = "Response"
        mock_response.tokens_used = 100
        mock_response.truncated = False
        mock_unified.chat_completion.return_value = mock_response
        mock_config.unified_client = mock_unified

        # Configure mock to return specific values
        mock_config.get_model_for_task = Mock(return_value="gpt-4o")
        mock_config.get_provider_for_task = Mock(return_value="openai")
        mock_config.get_temperature_for_task = Mock(return_value=0.7)
        mock_config.get_max_tokens_for_task = Mock(return_value=2000)

        client = APIClient(mock_config)
        messages = [{"role": "user", "content": "Test"}]
        client.make_api_call(messages, task="vision")

        # Verify task-based config methods were called
        mock_config.get_model_for_task.assert_called_once_with("vision")
        mock_config.get_provider_for_task.assert_called_once_with("vision")
        mock_config.get_temperature_for_task.assert_called_once_with("vision")
        mock_config.get_max_tokens_for_task.assert_called_once_with("vision")

    def test_token_tracking(self, mock_config):
        """Test token usage is tracked correctly."""
        mock_unified = Mock()

        # Multiple responses with different token counts
        responses = [
            Mock(content="Response 1", tokens_used=100, truncated=False),
            Mock(content="Response 2", tokens_used=200, truncated=False),
            Mock(content="Response 3", tokens_used=150, truncated=False)
        ]
        mock_unified.chat_completion.side_effect = responses
        mock_config.unified_client = mock_unified

        client = APIClient(mock_config)
        messages = [{"role": "user", "content": "Test"}]

        # Make multiple calls
        _, tokens1 = client.make_api_call(messages, task="main")
        _, tokens2 = client.make_api_call(messages, task="main")
        _, tokens3 = client.make_api_call(messages, task="main")

        assert tokens1 == 100
        assert tokens2 == 200
        assert tokens3 == 150

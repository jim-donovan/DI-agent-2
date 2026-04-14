"""Tests for BaseAgent and AgentResponse."""
import pytest
from agent_base import BaseAgent, AgentResponse

class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    def process(self, input_data, context=None):
        """Simple process implementation."""
        return AgentResponse(
            success=True,
            content="Processed successfully",
            confidence=0.9,
            metadata={"test": "data"},
            reasoning_steps=["Step 1", "Step 2"]
        )

    def get_system_prompt(self):
        """Return test system prompt."""
        return "Test system prompt"

@pytest.mark.unit
class TestAgentResponse:
    """Test AgentResponse dataclass."""

    def test_agent_response_creation(self):
        """Test creating AgentResponse."""
        response = AgentResponse(
            success=True,
            content="Test content",
            confidence=0.8,
            metadata={"key": "value"},
            reasoning_steps=["step1"]
        )

        assert response.success is True
        assert response.content == "Test content"
        assert response.confidence == 0.8
        assert response.metadata["key"] == "value"
        assert response.reasoning_steps == ["step1"]

    def test_agent_response_defaults(self):
        """Test AgentResponse with default values."""
        response = AgentResponse(
            success=False,
            content="Error message",
            confidence=0.0
        )

        assert response.success is False
        assert response.content == "Error message"
        assert response.confidence == 0.0
        assert response.metadata == {}
        assert response.reasoning_steps == []

    def test_agent_response_to_dict(self):
        """Test converting AgentResponse to dict."""
        response = AgentResponse(
            success=True,
            content="Test",
            confidence=0.9,
            metadata={"test": "data"},
            reasoning_steps=["step1"]
        )

        result = {
            "success": response.success,
            "content": response.content,
            "confidence": response.confidence,
            "metadata": response.metadata,
            "reasoning_steps": response.reasoning_steps
        }

        assert result["success"] is True
        assert result["content"] == "Test"
        assert result["confidence"] == 0.9

@pytest.mark.unit
class TestBaseAgent:
    """Test BaseAgent abstract class."""

    def test_concrete_agent_initialization(self, mock_logger, mock_api_client):
        """Test concrete agent can be initialized."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            logger=mock_logger,
            api_client=mock_api_client
        )

        assert agent.agent_id == "test_agent"
        assert agent.logger == mock_logger
        assert agent.api_client == mock_api_client

    def test_concrete_agent_process(self, mock_logger, mock_api_client):
        """Test concrete agent process method."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            logger=mock_logger,
            api_client=mock_api_client
        )

        result = agent.process({"test": "input"})

        assert isinstance(result, AgentResponse)
        assert result.success is True
        assert result.content == "Processed successfully"
        assert result.confidence == 0.9

    def test_agent_system_prompt(self, mock_logger, mock_api_client):
        """Test agent system prompt."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            logger=mock_logger,
            api_client=mock_api_client
        )

        prompt = agent.get_system_prompt()

        assert prompt == "Test system prompt"

    def test_agent_make_api_call(self, mock_logger, mock_api_client):
        """Test agent API call delegation."""
        agent = ConcreteAgent(
            agent_id="test_agent",
            logger=mock_logger,
            api_client=mock_api_client
        )

        messages = [{"role": "user", "content": "test"}]
        response, tokens = agent.make_api_call(messages, task="main")

        mock_api_client.make_api_call.assert_called_once_with(
            messages=messages,
            model=None,
            temperature=None,
            max_tokens=None,
            task="main"
        )
        assert response == "Test response"
        assert tokens == 100

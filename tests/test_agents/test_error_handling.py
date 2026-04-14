"""Tests for error handling across agents."""
import pytest
from unittest.mock import Mock, patch
from agent_base import BaseAgent, AgentResponse

class TestAgent(BaseAgent):
    """Test agent for error handling scenarios."""

    def process(self, input_data, context=None):
        """Process with error handling."""
        try:
            if not input_data:
                return AgentResponse(
                    success=False,
                    content="No input data provided",
                    confidence=0.0,
                    metadata={"error": "EmptyInput"}
                )

            if "error" in input_data:
                raise ValueError("Test error from input")

            return AgentResponse(
                success=True,
                content="Success",
                confidence=0.9
            )
        except Exception as e:
            self.logger.log_error(f"Error in process: {str(e)}")
            return AgentResponse(
                success=False,
                content=str(e),
                confidence=0.0,
                metadata={"error": type(e).__name__}
            )

    def get_system_prompt(self):
        return "Test prompt"

@pytest.mark.unit
class TestAgentErrorHandling:
    """Test error handling in agents."""

    def test_agent_handles_empty_input(self, mock_logger, mock_api_client):
        """Test agent handles empty input gracefully."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process(None)

        assert result.success is False
        assert "No input data" in result.content
        assert result.metadata["error"] == "EmptyInput"

    def test_agent_handles_exception_in_process(self, mock_logger, mock_api_client):
        """Test agent handles exceptions in process method."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"error": True})

        assert result.success is False
        assert "Test error" in result.content
        assert result.metadata["error"] == "ValueError"
        mock_logger.log_error.assert_called_once()

    def test_agent_returns_proper_error_response(self, mock_logger, mock_api_client):
        """Test agent returns proper error response structure."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"error": True})

        assert isinstance(result, AgentResponse)
        assert hasattr(result, 'success')
        assert hasattr(result, 'content')
        assert hasattr(result, 'metadata')
        assert result.success is False

    @patch('agent_base.BaseAgent.make_api_call')
    def test_agent_handles_api_failure(self, mock_make_api_call, mock_logger, mock_api_client):
        """Test agent handles API call failures."""
        # Make API call raise exception
        mock_make_api_call.side_effect = Exception("API Error")

        agent = TestAgent("test", mock_logger, mock_api_client)

        try:
            agent.make_api_call([{"role": "user", "content": "test"}])
        except Exception as e:
            assert "API Error" in str(e)

    def test_agent_validates_input_structure(self, mock_logger, mock_api_client):
        """Test agent validates input structure."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        # Test with invalid input type
        result = agent.process([])  # Empty list instead of dict

        # Agent should handle gracefully
        assert isinstance(result, AgentResponse)

    def test_agent_error_metadata_populated(self, mock_logger, mock_api_client):
        """Test error metadata is properly populated."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"error": True})

        assert "error" in result.metadata
        assert result.metadata["error"] == "ValueError"

    def test_agent_logs_errors(self, mock_logger, mock_api_client):
        """Test agent logs errors properly."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"error": True})

        # Verify logger was called
        mock_logger.log_error.assert_called()
        call_args = mock_logger.log_error.call_args[0][0]
        assert "Error in process" in call_args

    def test_agent_confidence_zero_on_error(self, mock_logger, mock_api_client):
        """Test agent sets confidence to 0 on error."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"error": True})

        assert result.confidence == 0.0

    def test_agent_handles_missing_required_fields(self, mock_logger, mock_api_client):
        """Test agent handles missing required fields."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        # Empty input
        result = agent.process({})

        # Should succeed (no required fields in test agent)
        assert isinstance(result, AgentResponse)

    def test_agent_error_response_serializable(self, mock_logger, mock_api_client):
        """Test error response can be serialized."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"error": True})

        # Should be able to convert to dict without errors
        response_dict = {
            "success": result.success,
            "content": result.content,
            "confidence": result.confidence,
            "metadata": result.metadata,
            "reasoning_steps": result.reasoning_steps
        }

        assert isinstance(response_dict, dict)
        assert response_dict["success"] is False

@pytest.mark.unit
class TestAgentInputValidation:
    """Test input validation in agents."""

    def test_agent_validates_data_types(self, mock_logger, mock_api_client):
        """Test agent validates input data types."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        # Test with string instead of dict
        result = agent.process("invalid")

        assert isinstance(result, AgentResponse)

    def test_agent_handles_none_context(self, mock_logger, mock_api_client):
        """Test agent handles None context."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"test": "data"}, context=None)

        assert isinstance(result, AgentResponse)
        assert result.success is True

    def test_agent_handles_empty_context(self, mock_logger, mock_api_client):
        """Test agent handles empty context."""
        agent = TestAgent("test", mock_logger, mock_api_client)

        result = agent.process({"test": "data"}, context={})

        assert isinstance(result, AgentResponse)
        assert result.success is True

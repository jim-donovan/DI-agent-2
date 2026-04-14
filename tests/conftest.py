"""Shared fixtures for pytest."""
import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock
from PIL import Image
import io

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.log_step = Mock()
    logger.log_success = Mock()
    logger.log_error = Mock()
    logger.log_warning = Mock()
    return logger

@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = Mock()
    # Set a reasonable default that tests can override
    client.make_api_call.return_value = ("Mock extracted text", 100)
    return client

@pytest.fixture
def sample_image():
    """Create sample test image."""
    img = Image.new('RGB', (800, 600), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.openai_api_key = "test-openai-key"
    config.anthropic_api_key = "test-anthropic-key"
    config.openai_model = "gpt-4o"
    config.anthropic_model = "claude-sonnet-4-20250514"
    config.dpi = 300
    config.vision_threshold = 0.1
    config.max_vision_calls = 100
    config.temperature = 0.0
    config.max_tokens = 4096
    config.enable_content_formatting_agent = True
    return config

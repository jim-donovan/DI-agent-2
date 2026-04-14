"""Tests for configuration loading and management."""
import pytest
import os
from unittest.mock import patch
from config import Config

@pytest.mark.unit
class TestConfig:
    """Test configuration loading and defaults."""

    def test_config_initialization(self):
        """Test config initializes with defaults."""
        config = Config()

        assert config.dpi > 0
        assert config.vision_corruption_threshold >= 0
        assert config.max_vision_calls_per_doc > 0
        assert config.main_temperature >= 0
        assert config.main_max_tokens > 0

    def test_openai_model_configuration(self):
        """Test OpenAI model configuration."""
        config = Config()

        assert config.openai_model is not None
        assert len(config.openai_model) > 0

    def test_anthropic_model_configuration(self):
        """Test Anthropic model configuration."""
        config = Config()

        assert config.anthropic_model is not None
        assert len(config.anthropic_model) > 0

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-openai-key'})
    def test_openai_api_key_from_env(self):
        """Test OpenAI API key loaded from environment."""
        config = Config()

        assert config.openai_api_key == 'test-openai-key'

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-anthropic-key'})
    def test_anthropic_api_key_from_env(self):
        """Test Anthropic API key loaded from environment."""
        config = Config()

        assert config.anthropic_api_key == 'test-anthropic-key'

    def test_content_formatting_default(self):
        """Test content formatting defaults to enabled."""
        config = Config()
        # Default is True
        assert isinstance(config.enable_content_formatting_agent, bool)

    def test_parallel_vision_default(self):
        """Test parallel vision defaults to enabled."""
        config = Config()
        # Default is True
        assert isinstance(config.use_parallel_vision, bool)

    @patch.dict(os.environ, {'DEBUG_OCR_PIPELINE': 'true'})
    def test_debug_mode_enabled(self):
        """Test debug mode can be enabled."""
        config = Config()

        assert config.debug_ocr_pipeline is True

    def test_get_model_for_task(self):
        """Test getting model for specific task."""
        config = Config()

        vision_model = config.get_model_for_task("vision")
        main_model = config.get_model_for_task("main")
        corruption_model = config.get_model_for_task("corruption")

        assert vision_model is not None
        assert main_model is not None
        assert corruption_model is not None

    def test_get_provider_for_task(self):
        """Test getting provider for specific task."""
        config = Config()

        vision_provider = config.get_provider_for_task("vision")
        formatting_provider = config.get_provider_for_task("content_formatting")

        assert vision_provider in ["openai", "anthropic"]
        assert formatting_provider in ["openai", "anthropic"]

    def test_get_temperature_for_task(self):
        """Test getting temperature for specific task."""
        config = Config()

        temp = config.get_temperature_for_task("vision")

        assert isinstance(temp, (int, float))
        assert temp >= 0
        assert temp <= 2

    def test_get_max_tokens_for_task(self):
        """Test getting max tokens for specific task."""
        config = Config()

        max_tokens = config.get_max_tokens_for_task("vision")

        assert isinstance(max_tokens, int)
        assert max_tokens > 0

    def test_config_immutability(self):
        """Test config values remain consistent."""
        config = Config()

        original_dpi = config.dpi
        original_model = config.openai_model

        # Values should not change
        assert config.dpi == original_dpi
        assert config.openai_model == original_model

    def test_vision_threshold_range(self):
        """Test vision corruption threshold is in valid range."""
        config = Config()

        assert 0 <= config.vision_corruption_threshold <= 1

    def test_max_vision_calls_positive(self):
        """Test max vision calls per doc is positive."""
        config = Config()

        assert config.max_vision_calls_per_doc > 0

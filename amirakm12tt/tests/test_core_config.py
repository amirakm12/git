"""
Tests for core.config module
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from core.config import (
    SystemConfig, AIModelConfig, RAGConfig, SpeculativeDecodingConfig,
    KernelConfig, SensorConfig, AgentConfig, UIConfig, SecurityConfig, MonitoringConfig
)


class TestAIModelConfig:
    """Test AIModelConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = AIModelConfig()
        assert config.model_name == "gpt-4"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.timeout == 30


class TestRAGConfig:
    """Test RAGConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RAGConfig()
        assert config.vector_db_path == "data/vector_db"
        assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.similarity_threshold == 0.7
        assert config.max_retrieved_docs == 5


class TestSensorConfig:
    """Test SensorConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = SensorConfig()
        assert config.enabled_sensors == ["cpu", "memory", "disk", "network", "gpu"]
        assert config.fusion_algorithm == "kalman_filter"
        assert config.sampling_rate == 100
        assert config.buffer_size == 1000
        assert config.calibration_enabled == True
    
    def test_post_init(self):
        """Test post-initialization behavior."""
        config = SensorConfig(enabled_sensors=None)
        assert config.enabled_sensors == ["cpu", "memory", "disk", "network", "gpu"]


class TestMonitoringConfig:
    """Test MonitoringConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = MonitoringConfig()
        assert config.metrics_enabled == True
        assert config.metrics_port == 9090
        assert config.log_retention_days == 30
        assert config.performance_monitoring == True
    
    def test_alert_thresholds_post_init(self):
        """Test alert thresholds post-initialization."""
        config = MonitoringConfig(alert_thresholds=None)
        expected_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 5.0
        }
        assert config.alert_thresholds == expected_thresholds


class TestSystemConfig:
    """Test SystemConfig class."""
    
    def test_initialization(self, temp_dir):
        """Test system config initialization."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        assert config.system_name == "AI-System-v1.0"
        assert config.environment == "development"
        assert isinstance(config.ai_model, AIModelConfig)
        assert isinstance(config.rag, RAGConfig)
        assert isinstance(config.sensors, SensorConfig)
    
    def test_create_directories(self, temp_dir):
        """Test directory creation."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        # Check that directories were created
        assert config.data_dir.exists()
        assert config.logs_dir.exists()
        assert config.temp_dir.exists()
    
    def test_load_config_file_not_exists(self, temp_dir):
        """Test loading config when file doesn't exist."""
        config_file = temp_dir / "nonexistent_config.json"
        config = SystemConfig(str(config_file))
        
        # Should use defaults and create config file
        assert config_file.exists()
    
    def test_load_config_file_exists(self, temp_dir):
        """Test loading config from existing file."""
        config_file = temp_dir / "test_config.json"
        
        # Create a test config file
        test_config_data = {
            "ai_model": {
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.5
            },
            "ui": {
                "dashboard_port": 9000
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config_data, f)
        
        config = SystemConfig(str(config_file))
        
        assert config.ai_model.model_name == "gpt-3.5-turbo"
        assert config.ai_model.temperature == 0.5
        assert config.ui.dashboard_port == 9000
    
    def test_save_config(self, temp_dir):
        """Test saving configuration to file."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        # Modify some values
        config.ai_model.temperature = 0.8
        config.ui.dashboard_port = 8888
        
        # Save config
        config.save_config()
        
        # Verify file was written
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['ai_model']['temperature'] == 0.8
        assert saved_data['ui']['dashboard_port'] == 8888
    
    def test_env_overrides(self, temp_dir):
        """Test environment variable overrides."""
        config_file = temp_dir / "test_config.json"
        
        with patch.dict(os.environ, {
            'AI_MODEL_NAME': 'gpt-3.5-turbo',
            'AI_MODEL_TEMPERATURE': '0.3',
            'DASHBOARD_PORT': '7777',
            'VOICE_ENABLED': 'false',
            'DEBUG_MODE': 'true'
        }):
            config = SystemConfig(str(config_file))
        
        assert config.ai_model.model_name == 'gpt-3.5-turbo'
        assert config.ai_model.temperature == 0.3
        assert config.ui.dashboard_port == 7777
        assert config.ui.voice_enabled == False
        assert config.debug_mode == True
    
    def test_encryption_initialization(self, temp_dir):
        """Test encryption system initialization."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        assert config.encryption_key is not None
        if config.security.encryption_enabled:
            assert config.cipher_suite is not None
    
    def test_api_key_management(self, temp_dir):
        """Test API key storage and retrieval."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        # Test setting API key
        test_key = "test_api_key_12345"
        config.set_api_key("openai", test_key)
        
        # Test retrieving API key
        retrieved_key = config.get_api_key("openai")
        assert retrieved_key == test_key
    
    def test_api_key_from_environment(self, temp_dir):
        """Test API key retrieval from environment."""
        config_file = temp_dir / "test_config.json"
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env_api_key'}):
            config = SystemConfig(str(config_file))
            api_key = config.get_api_key("openai")
            assert api_key == 'env_api_key'
    
    def test_validate_config_success(self, temp_dir):
        """Test successful configuration validation."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        assert config.validate_config() == True
    
    def test_validate_config_invalid_port(self, temp_dir):
        """Test configuration validation with invalid port."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        config.ui.dashboard_port = 99999  # Invalid port
        assert config.validate_config() == False
    
    def test_validate_config_invalid_temperature(self, temp_dir):
        """Test configuration validation with invalid temperature."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        config.ai_model.temperature = 5.0  # Invalid temperature
        assert config.validate_config() == False
    
    def test_validate_config_invalid_similarity_threshold(self, temp_dir):
        """Test configuration validation with invalid similarity threshold."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        config.rag.similarity_threshold = 1.5  # Invalid threshold
        assert config.validate_config() == False
    
    def test_to_dict(self, temp_dir):
        """Test configuration conversion to dictionary."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        config_dict = config.to_dict()
        
        assert 'ai_model' in config_dict
        assert 'rag' in config_dict
        assert 'system' in config_dict
        assert config_dict['system']['name'] == "AI-System-v1.0"
    
    def test_dashboard_port_property(self, temp_dir):
        """Test dashboard_port property for backward compatibility."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        assert config.dashboard_port == config.ui.dashboard_port
    
    def test_repr(self, temp_dir):
        """Test string representation."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        
        repr_str = repr(config)
        assert "SystemConfig" in repr_str
        assert config.environment in repr_str
        assert str(config.debug_mode) in repr_str
    
    def test_encryption_disabled(self, temp_dir):
        """Test behavior when encryption is disabled."""
        config_file = temp_dir / "test_config.json"
        config = SystemConfig(str(config_file))
        config.security.encryption_enabled = False
        config._init_encryption()
        
        test_data = "sensitive_data"
        encrypted = config.encrypt_data(test_data)
        decrypted = config.decrypt_data(encrypted)
        
        # When encryption is disabled, data should pass through unchanged
        assert encrypted == test_data
        assert decrypted == test_data
    
    def test_malformed_config_file(self, temp_dir):
        """Test handling of malformed config file."""
        config_file = temp_dir / "malformed_config.json"
        
        # Create malformed JSON file
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should handle gracefully and use defaults
        config = SystemConfig(str(config_file))
        assert config.ai_model.model_name == "gpt-4"  # Default value


@pytest.mark.integration
class TestSystemConfigIntegration:
    """Integration tests for SystemConfig."""
    
    def test_full_config_lifecycle(self, temp_dir):
        """Test complete configuration lifecycle."""
        config_file = temp_dir / "lifecycle_config.json"
        
        # Create initial config
        config1 = SystemConfig(str(config_file))
        config1.ai_model.temperature = 0.9
        config1.ui.dashboard_port = 9999
        config1.save_config()
        
        # Load config in new instance
        config2 = SystemConfig(str(config_file))
        
        assert config2.ai_model.temperature == 0.9
        assert config2.ui.dashboard_port == 9999
    
    def test_config_with_env_and_file(self, temp_dir):
        """Test configuration with both file and environment overrides."""
        config_file = temp_dir / "env_file_config.json"
        
        # Create config file
        file_config = {
            "ai_model": {"temperature": 0.5},
            "ui": {"dashboard_port": 8000}
        }
        with open(config_file, 'w') as f:
            json.dump(file_config, f)
        
        # Load with environment overrides
        with patch.dict(os.environ, {
            'AI_MODEL_TEMPERATURE': '0.8',  # Should override file
            'VOICE_ENABLED': 'true'  # Not in file, should be applied
        }):
            config = SystemConfig(str(config_file))
        
        assert config.ai_model.temperature == 0.8  # From env
        assert config.ui.dashboard_port == 8000  # From file
        assert config.ui.voice_enabled == True  # From env
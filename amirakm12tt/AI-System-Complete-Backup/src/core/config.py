"""
System Configuration Module
Manages all system settings, parameters, and environment variables
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

@dataclass
class AIModelConfig:
    """Configuration for AI models."""
    model_name: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    
@dataclass
class RAGConfig:
    """Configuration for RAG system."""
    vector_db_path: str = "data/vector_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_threshold: float = 0.7
    max_retrieved_docs: int = 5
    
@dataclass
class SpeculativeDecodingConfig:
    """Configuration for speculative decoding."""
    draft_model: str = "gpt-3.5-turbo"
    target_model: str = "gpt-4"
    speculation_length: int = 5
    acceptance_threshold: float = 0.8
    max_speculation_depth: int = 3
    
@dataclass
class KernelConfig:
    """Configuration for kernel-level integration."""
    driver_path: str = "drivers/"
    enable_monitoring: bool = True
    monitoring_interval: int = 1000  # milliseconds
    log_level: str = "INFO"
    security_enabled: bool = True
    
@dataclass
class SensorConfig:
    """Configuration for sensor fusion."""
    enabled_sensors: list = None
    fusion_algorithm: str = "kalman_filter"
    sampling_rate: int = 100  # Hz
    buffer_size: int = 1000
    calibration_enabled: bool = True
    
    def __post_init__(self):
        if self.enabled_sensors is None:
            self.enabled_sensors = ["cpu", "memory", "disk", "network", "gpu"]
            
@dataclass
class AgentConfig:
    """Configuration for AI agents."""
    max_concurrent_tasks: int = 10
    task_timeout: int = 300  # seconds
    retry_attempts: int = 3
    communication_protocol: str = "async_queue"
    
@dataclass
class UIConfig:
    """Configuration for user interfaces."""
    dashboard_port: int = 8080
    dashboard_host: str = "0.0.0.0"
    voice_enabled: bool = True
    voice_language: str = "en-US"
    theme: str = "dark"
    
@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    encryption_enabled: bool = True
    key_rotation_interval: int = 86400  # seconds (24 hours)
    audit_logging: bool = True
    access_control_enabled: bool = True
    max_login_attempts: int = 3
    session_timeout: int = 3600  # seconds
    
@dataclass
class MonitoringConfig:
    """Configuration for system monitoring."""
    metrics_enabled: bool = True
    metrics_port: int = 9090
    log_retention_days: int = 30
    alert_thresholds: Dict[str, float] = None
    performance_monitoring: bool = True
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "response_time": 5.0
            }

class SystemConfig:
    """Main system configuration class."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/system_config.json"
        self.config_dir = Path(self.config_file).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration sections
        self.ai_model = AIModelConfig()
        self.rag = RAGConfig()
        self.speculative_decoding = SpeculativeDecodingConfig()
        self.kernel = KernelConfig()
        self.sensors = SensorConfig()
        self.agents = AgentConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        
        # System-wide settings
        self.system_name = "AI-System-v1.0"
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.temp_dir = Path("temp")
        
        # Create necessary directories
        self._create_directories()
        
        # Load configuration from file if exists
        self.load_config()
        
        # Override with environment variables
        self._load_env_overrides()
        
        # Initialize encryption
        self._init_encryption()
        
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.temp_dir,
            Path(self.rag.vector_db_path).parent,
            Path(self.kernel.driver_path)
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _init_encryption(self):
        """Initialize encryption system."""
        key_file = self.config_dir / "encryption.key"
        
        if key_file.exists() and self.security.encryption_enabled:
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            if self.security.encryption_enabled:
                with open(key_file, 'wb') as f:
                    f.write(key)
                # Secure the key file
                os.chmod(key_file, 0o600)
                
        self.encryption_key = key
        self.cipher_suite = Fernet(key) if self.security.encryption_enabled else None
        
    def load_config(self):
        """Load configuration from file."""
        if not Path(self.config_file).exists():
            logger.info(f"Config file {self.config_file} not found, using defaults")
            self.save_config()
            return
            
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                
            # Update configuration objects
            for section_name, section_data in config_data.items():
                if hasattr(self, section_name):
                    section_obj = getattr(self, section_name)
                    for key, value in section_data.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
                            
            logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            
    def save_config(self):
        """Save current configuration to file."""
        config_data = {}
        
        # Collect all configuration sections
        sections = [
            'ai_model', 'rag', 'speculative_decoding', 'kernel',
            'sensors', 'agents', 'ui', 'security', 'monitoring'
        ]
        
        for section_name in sections:
            if hasattr(self, section_name):
                section_obj = getattr(self, section_name)
                config_data[section_name] = asdict(section_obj)
                
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'AI_MODEL_NAME': ('ai_model', 'model_name'),
            'AI_MODEL_TEMPERATURE': ('ai_model', 'temperature', float),
            'RAG_CHUNK_SIZE': ('rag', 'chunk_size', int),
            'RAG_SIMILARITY_THRESHOLD': ('rag', 'similarity_threshold', float),
            'DASHBOARD_PORT': ('ui', 'dashboard_port', int),
            'VOICE_ENABLED': ('ui', 'voice_enabled', lambda x: x.lower() == 'true'),
            'SECURITY_ENABLED': ('security', 'encryption_enabled', lambda x: x.lower() == 'true'),
            'DEBUG_MODE': ('system', 'debug_mode', lambda x: x.lower() == 'true'),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    section_name, attr_name = config_path[:2]
                    converter = config_path[2] if len(config_path) > 2 else str
                    
                    if section_name == 'system':
                        setattr(self, attr_name, converter(env_value))
                    else:
                        section_obj = getattr(self, section_name)
                        setattr(section_obj, attr_name, converter(env_value))
                        
                    logger.info(f"Override {section_name}.{attr_name} from environment")
                except Exception as e:
                    logger.error(f"Error applying environment override {env_var}: {e}")
                    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self.security.encryption_enabled or not self.cipher_suite:
            return data
        return self.cipher_suite.encrypt(data.encode()).decode()
        
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self.security.encryption_enabled or not self.cipher_suite:
            return encrypted_data
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service."""
        env_var = f"{service.upper()}_API_KEY"
        api_key = os.getenv(env_var)
        
        if not api_key:
            # Try to load from encrypted storage
            key_file = self.config_dir / f"{service}_key.enc"
            if key_file.exists():
                try:
                    with open(key_file, 'r') as f:
                        encrypted_key = f.read()
                    api_key = self.decrypt_data(encrypted_key)
                except Exception as e:
                    logger.error(f"Error loading API key for {service}: {e}")
                    
        return api_key
        
    def set_api_key(self, service: str, api_key: str):
        """Set API key for a service."""
        key_file = self.config_dir / f"{service}_key.enc"
        try:
            encrypted_key = self.encrypt_data(api_key)
            with open(key_file, 'w') as f:
                f.write(encrypted_key)
            os.chmod(key_file, 0o600)
            logger.info(f"API key for {service} saved securely")
        except Exception as e:
            logger.error(f"Error saving API key for {service}: {e}")
            
    def validate_config(self) -> bool:
        """Validate the current configuration."""
        errors = []
        
        # Validate ports
        if not (1024 <= self.ui.dashboard_port <= 65535):
            errors.append("Dashboard port must be between 1024 and 65535")
            
        # Validate file paths
        required_dirs = [self.data_dir, self.logs_dir]
        for directory in required_dirs:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {directory}: {e}")
                    
        # Validate AI model settings
        if self.ai_model.temperature < 0 or self.ai_model.temperature > 2:
            errors.append("AI model temperature must be between 0 and 2")
            
        if self.ai_model.max_tokens <= 0:
            errors.append("AI model max_tokens must be positive")
            
        # Validate RAG settings
        if self.rag.similarity_threshold < 0 or self.rag.similarity_threshold > 1:
            errors.append("RAG similarity threshold must be between 0 and 1")
            
        # Validate API keys for production environment
        if self.environment == 'production':
            if not self.get_api_key('openai'):
                errors.append("OpenAI API key is required in production environment")
            
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
            
        logger.info("Configuration validation passed")
        return True
        
    @property
    def dashboard_port(self) -> int:
        """Get dashboard port for backward compatibility."""
        return self.ui.dashboard_port
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        sections = [
            'ai_model', 'rag', 'speculative_decoding', 'kernel',
            'sensors', 'agents', 'ui', 'security', 'monitoring'
        ]
        
        for section_name in sections:
            if hasattr(self, section_name):
                section_obj = getattr(self, section_name)
                result[section_name] = asdict(section_obj)
                
        # Add system-wide settings
        result['system'] = {
            'name': self.system_name,
            'debug_mode': self.debug_mode,
            'environment': self.environment
        }
        
        return result
        
    def __repr__(self):
        return f"SystemConfig(environment={self.environment}, debug={self.debug_mode})"
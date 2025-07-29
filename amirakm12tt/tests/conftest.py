"""
Pytest configuration and common fixtures for AI System tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import SystemConfig


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config = SystemConfig()
    
    # Override paths to use temp directory
    config.data_dir = temp_dir / "data"
    config.logs_dir = temp_dir / "logs"
    config.temp_dir = temp_dir / "temp"
    config.rag.vector_db_path = str(temp_dir / "vector_db")
    config.kernel.driver_path = str(temp_dir / "drivers")
    
    # Create directories
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    config.temp_dir.mkdir(parents=True, exist_ok=True)
    Path(config.rag.vector_db_path).mkdir(parents=True, exist_ok=True)
    Path(config.kernel.driver_path).mkdir(parents=True, exist_ok=True)
    
    # Set test-friendly values
    config.ui.dashboard_port = 8081  # Use different port for tests
    config.ui.voice_enabled = False  # Disable voice for tests
    config.debug_mode = True
    
    return config


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model for testing."""
    mock_model = Mock()
    mock_model.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
    return mock_model


@pytest.fixture
def mock_vector_db():
    """Mock vector database for testing."""
    mock_db = Mock()
    mock_db.add = Mock()
    mock_db.query = Mock(return_value=Mock(documents=[["Test document"]], metadatas=[[{"source": "test"}]]))
    return mock_db


@pytest.fixture
def sample_sensor_data():
    """Sample sensor data for testing."""
    return {
        'cpu_usage': 45.5,
        'memory_usage': 67.2,
        'disk_usage': 23.8,
        'network_usage': 1024.0,
        'timestamp': 1234567890.0
    }


@pytest.fixture
def sample_rag_documents():
    """Sample documents for RAG testing."""
    return [
        {
            'content': 'This is a test document about artificial intelligence.',
            'metadata': {'source': 'test1.txt', 'category': 'AI'}
        },
        {
            'content': 'Machine learning is a subset of artificial intelligence.',
            'metadata': {'source': 'test2.txt', 'category': 'ML'}
        },
        {
            'content': 'Neural networks are inspired by biological neurons.',
            'metadata': {'source': 'test3.txt', 'category': 'Neural'}
        }
    ]


@pytest.fixture
def mock_system_resources():
    """Mock system resource data."""
    return {
        'cpu_percent': 25.5,
        'memory_percent': 45.2,
        'disk_usage': {'total': 1000000, 'used': 300000, 'free': 700000},
        'network_io': {'bytes_sent': 1024, 'bytes_recv': 2048},
        'processes': [{'pid': 1234, 'name': 'test_process', 'cpu_percent': 5.0}]
    }


# Async test helpers
@pytest.fixture
def async_mock():
    """Create an async mock."""
    return AsyncMock()


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "security: mark test as a security test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add unit marker to all tests by default
        if not any(marker.name in ['integration', 'performance', 'security'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
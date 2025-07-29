"""
Tests for core.orchestrator module
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from core.orchestrator import (
    SystemOrchestrator, SystemState, ComponentStatus, SystemMetrics
)


class TestComponentStatus:
    """Test ComponentStatus dataclass."""
    
    def test_creation(self):
        """Test component status creation."""
        status = ComponentStatus(
            name="test_component",
            state="running",
            health="healthy",
            last_heartbeat=time.time(),
            error_count=0,
            performance_metrics={}
        )
        
        assert status.name == "test_component"
        assert status.state == "running"
        assert status.health == "healthy"
        assert status.error_count == 0


class TestSystemMetrics:
    """Test SystemMetrics dataclass."""
    
    def test_creation(self):
        """Test system metrics creation."""
        metrics = SystemMetrics(
            uptime=100.0,
            total_requests=50,
            successful_requests=45,
            failed_requests=5,
            average_response_time=0.5,
            active_components=10,
            memory_usage=75.0,
            cpu_usage=25.0
        )
        
        assert metrics.uptime == 100.0
        assert metrics.total_requests == 50
        assert metrics.successful_requests == 45
        assert metrics.failed_requests == 5


class TestSystemOrchestrator:
    """Test SystemOrchestrator class."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        components = {}
        for name in ['test_component1', 'test_component2', 'test_component3']:
            mock_component = Mock()
            mock_component.health_check = AsyncMock(return_value="healthy")
            mock_component.execute_task = AsyncMock(return_value="task_result")
            components[name] = mock_component
        return components
    
    @pytest.fixture
    def orchestrator(self, test_config, mock_components):
        """Create orchestrator instance for testing."""
        return SystemOrchestrator(test_config, mock_components)
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.state == SystemState.INITIALIZING
        assert orchestrator.is_running == False
        assert len(orchestrator.component_status) == 0
        assert orchestrator.metrics.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_initialize(self, orchestrator):
        """Test orchestrator initialization."""
        await orchestrator.initialize()
        
        assert orchestrator.state == SystemState.STARTING
        assert len(orchestrator.component_status) == len(orchestrator.components)
        
        for component_name in orchestrator.components:
            assert component_name in orchestrator.component_status
            status = orchestrator.component_status[component_name]
            assert status.name == component_name
            assert status.state == "initialized"
    
    @pytest.mark.asyncio
    async def test_start(self, orchestrator):
        """Test orchestrator start."""
        await orchestrator.initialize()
        await orchestrator.start()
        
        assert orchestrator.is_running == True
        assert orchestrator.state == SystemState.RUNNING
        assert len(orchestrator.component_tasks) > 0
    
    @pytest.mark.asyncio
    async def test_shutdown(self, orchestrator):
        """Test orchestrator shutdown."""
        await orchestrator.initialize()
        await orchestrator.start()
        
        # Brief pause to let tasks start
        await asyncio.sleep(0.1)
        
        await orchestrator.shutdown()
        
        assert orchestrator.is_running == False
        assert orchestrator.state == SystemState.STOPPED
        assert len(orchestrator.component_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_submit_task(self, orchestrator):
        """Test task submission."""
        await orchestrator.initialize()
        
        task = {
            'type': 'test_task',
            'data': {'key': 'value'}
        }
        
        task_id = await orchestrator.submit_task(task)
        assert task_id is not None
        assert task_id.startswith('task_')
    
    @pytest.mark.asyncio
    async def test_task_routing(self, orchestrator):
        """Test task routing to components."""
        await orchestrator.initialize()
        
        # Test routing by component
        task = {
            'type': 'test_task',
            'component': 'test_component1',
            'data': {'key': 'value'}
        }
        
        result = await orchestrator._execute_task(task)
        assert result['success'] == True
        orchestrator.components['test_component1'].execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_routing_by_type(self, orchestrator):
        """Test task routing by type."""
        await orchestrator.initialize()
        
        # Mock specific agent components
        orchestrator.components['triage_agent'] = Mock()
        orchestrator.components['triage_agent'].process_request = AsyncMock(return_value="triage_result")
        
        task = {
            'type': 'triage',
            'data': {'query': 'test query'}
        }
        
        result = await orchestrator._execute_task(task)
        assert result['success'] == True
        orchestrator.components['triage_agent'].process_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_handling(self, orchestrator):
        """Test event handling."""
        await orchestrator.initialize()
        
        # Test component error event
        event = {
            'type': 'component_error',
            'component': 'test_component1',
            'error': 'Test error'
        }
        
        await orchestrator._handle_event(event)
        
        # Check that error count was incremented
        status = orchestrator.component_status['test_component1']
        assert status.error_count == 1
    
    @pytest.mark.asyncio
    async def test_component_failure_handling(self, orchestrator):
        """Test component failure handling."""
        await orchestrator.initialize()
        
        # Mock component with restart capability
        mock_component = Mock()
        mock_component.restart = AsyncMock()
        orchestrator.components['failing_component'] = mock_component
        orchestrator.component_status['failing_component'] = ComponentStatus(
            name='failing_component',
            state='running',
            health='healthy',
            last_heartbeat=time.time(),
            error_count=0,
            performance_metrics={}
        )
        
        await orchestrator._handle_component_failure('failing_component')
        
        mock_component.restart.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_performance_alert_handling(self, orchestrator):
        """Test performance alert handling."""
        await orchestrator.initialize()
        
        event = {
            'type': 'performance_alert',
            'metric': 'response_time',
            'value': 10.0,
            'threshold': 5.0
        }
        
        with patch.object(orchestrator, '_optimize_performance') as mock_optimize:
            await orchestrator._handle_event(event)
            mock_optimize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_security_alert_handling(self, orchestrator):
        """Test security alert handling."""
        await orchestrator.initialize()
        
        # Mock security monitor
        mock_security = Mock()
        mock_security.handle_alert = AsyncMock()
        orchestrator.components['security_monitor'] = mock_security
        
        event = {
            'type': 'security_alert',
            'alert_type': 'intrusion_attempt',
            'details': 'Suspicious activity detected'
        }
        
        await orchestrator._handle_event(event)
        mock_security.handle_alert.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_system_commands(self, orchestrator):
        """Test system command handling."""
        await orchestrator.initialize()
        
        with patch.object(orchestrator, 'pause_system') as mock_pause:
            event = {'type': 'system_command', 'command': 'pause'}
            await orchestrator._handle_event(event)
            mock_pause.assert_called_once()
        
        with patch.object(orchestrator, 'resume_system') as mock_resume:
            event = {'type': 'system_command', 'command': 'resume'}
            await orchestrator._handle_event(event)
            mock_resume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pause_resume_system(self, orchestrator):
        """Test system pause and resume."""
        await orchestrator.initialize()
        
        # Mock components with pause/resume methods
        for component in orchestrator.components.values():
            component.pause = AsyncMock()
            component.resume = AsyncMock()
        
        # Test pause
        await orchestrator.pause_system()
        assert orchestrator.state == SystemState.PAUSED
        
        for component in orchestrator.components.values():
            component.pause.assert_called_once()
        
        # Test resume
        await orchestrator.resume_system()
        assert orchestrator.state == SystemState.RUNNING
        
        for component in orchestrator.components.values():
            component.resume.assert_called_once()
    
    def test_get_system_status(self, orchestrator):
        """Test system status retrieval."""
        status = orchestrator.get_system_status()
        
        assert 'state' in status
        assert 'uptime' in status
        assert 'components' in status
        assert 'metrics' in status
        
        assert status['state'] == SystemState.INITIALIZING.value
    
    def test_get_component_status(self, orchestrator):
        """Test component status retrieval."""
        # Add a component status
        orchestrator.component_status['test_component'] = ComponentStatus(
            name='test_component',
            state='running',
            health='healthy',
            last_heartbeat=time.time(),
            error_count=0,
            performance_metrics={}
        )
        
        status = orchestrator.get_component_status('test_component')
        assert status is not None
        assert status['name'] == 'test_component'
        assert status['state'] == 'running'
        assert status['health'] == 'healthy'
        
        # Test non-existent component
        status = orchestrator.get_component_status('non_existent')
        assert status is None
    
    def test_response_time_tracking(self, orchestrator):
        """Test response time tracking."""
        # Add some response times
        orchestrator._update_response_time(0.5)
        orchestrator._update_response_time(1.0)
        orchestrator._update_response_time(0.8)
        
        assert len(orchestrator.response_times) == 3
        assert 0.5 in orchestrator.response_times
        assert 1.0 in orchestrator.response_times
        assert 0.8 in orchestrator.response_times
    
    def test_response_time_limit(self, orchestrator):
        """Test response time sample limit."""
        # Add more than max samples
        for i in range(orchestrator.max_response_time_samples + 100):
            orchestrator._update_response_time(float(i))
        
        # Should not exceed max samples
        assert len(orchestrator.response_times) == orchestrator.max_response_time_samples
        
        # Should contain the most recent samples
        assert float(orchestrator.max_response_time_samples + 99) in orchestrator.response_times
    
    @pytest.mark.asyncio
    async def test_publish_event(self, orchestrator):
        """Test event publishing."""
        await orchestrator.initialize()
        
        event = {
            'type': 'test_event',
            'data': {'key': 'value'}
        }
        
        await orchestrator.publish_event(event)
        
        # Event should be in the queue
        assert not orchestrator.event_bus.empty()
    
    @pytest.mark.asyncio
    async def test_get_result_timeout(self, orchestrator):
        """Test result retrieval with timeout."""
        await orchestrator.initialize()
        
        # Test timeout when no result is available
        result = await orchestrator.get_result('non_existent_task', timeout=0.1)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_result_success(self, orchestrator):
        """Test successful result retrieval."""
        await orchestrator.initialize()
        
        # Put a result in the queue
        test_result = {
            'task_id': 'test_task_123',
            'result': {'success': True, 'data': 'test_data'},
            'response_time': 0.5,
            'timestamp': time.time()
        }
        
        await orchestrator.result_queue.put(test_result)
        
        # Retrieve the result
        result = await orchestrator.get_result('test_task_123', timeout=1.0)
        assert result is not None
        assert result['task_id'] == 'test_task_123'
        assert result['result']['data'] == 'test_data'


@pytest.mark.integration
class TestSystemOrchestratorIntegration:
    """Integration tests for SystemOrchestrator."""
    
    @pytest.mark.asyncio
    async def test_full_orchestrator_lifecycle(self, test_config):
        """Test complete orchestrator lifecycle."""
        # Create mock components
        components = {}
        for name in ['component1', 'component2']:
            mock_comp = Mock()
            mock_comp.health_check = AsyncMock(return_value="healthy")
            mock_comp.execute_task = AsyncMock(return_value="result")
            components[name] = mock_comp
        
        orchestrator = SystemOrchestrator(test_config, components)
        
        try:
            # Initialize and start
            await orchestrator.initialize()
            await orchestrator.start()
            
            # Submit a task
            task_id = await orchestrator.submit_task({
                'type': 'test',
                'component': 'component1',
                'data': {}
            })
            
            # Wait briefly for processing
            await asyncio.sleep(0.1)
            
            # Check system status
            status = orchestrator.get_system_status()
            assert status['state'] == SystemState.RUNNING.value
            
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, test_config):
        """Test error recovery mechanisms."""
        # Create components with one that fails
        components = {
            'good_component': Mock(),
            'bad_component': Mock()
        }
        
        components['good_component'].health_check = AsyncMock(return_value="healthy")
        components['bad_component'].health_check = AsyncMock(side_effect=Exception("Component failed"))
        components['bad_component'].restart = AsyncMock()
        
        orchestrator = SystemOrchestrator(test_config, components)
        
        try:
            await orchestrator.initialize()
            await orchestrator.start()
            
            # Wait for health checks to run
            await asyncio.sleep(0.1)
            
            # Check that error was recorded
            bad_status = orchestrator.component_status['bad_component']
            assert bad_status.health == "unhealthy"
            assert bad_status.error_count > 0
            
        finally:
            await orchestrator.shutdown()
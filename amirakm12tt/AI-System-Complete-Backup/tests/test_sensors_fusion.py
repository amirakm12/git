"""
Tests for sensors.fusion module
"""

import pytest
import asyncio
import time
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from collections import deque

from sensors.fusion import (
    SensorFusionManager, SensorType, SensorReading, FusedData,
    KalmanFilter, WeightedAverageFilter, ParticleFilter
)


class TestSensorReading:
    """Test SensorReading dataclass."""
    
    def test_creation(self):
        """Test sensor reading creation."""
        reading = SensorReading(
            sensor_id="cpu_sensor_1",
            sensor_type=SensorType.CPU,
            value=45.5,
            unit="percent",
            timestamp=time.time(),
            quality=0.9
        )
        
        assert reading.sensor_id == "cpu_sensor_1"
        assert reading.sensor_type == SensorType.CPU
        assert reading.value == 45.5
        assert reading.unit == "percent"
        assert reading.quality == 0.9
        assert reading.metadata == {}
    
    def test_post_init_metadata(self):
        """Test metadata post-initialization."""
        reading = SensorReading(
            sensor_id="test_sensor",
            sensor_type=SensorType.MEMORY,
            value=67.2,
            unit="percent",
            timestamp=time.time(),
            metadata=None
        )
        
        assert reading.metadata == {}


class TestFusedData:
    """Test FusedData dataclass."""
    
    def test_creation(self):
        """Test fused data creation."""
        fused = FusedData(
            sensor_types=[SensorType.CPU, SensorType.MEMORY],
            fused_value=56.3,
            confidence=0.85,
            timestamp=time.time(),
            contributing_sensors=["cpu_1", "memory_1"],
            fusion_method="kalman_filter"
        )
        
        assert len(fused.sensor_types) == 2
        assert SensorType.CPU in fused.sensor_types
        assert fused.fused_value == 56.3
        assert fused.confidence == 0.85
        assert fused.fusion_method == "kalman_filter"


class TestKalmanFilter:
    """Test KalmanFilter class."""
    
    def test_initialization(self):
        """Test Kalman filter initialization."""
        kf = KalmanFilter(process_variance=1e-3, measurement_variance=1e-1)
        
        assert kf.process_variance == 1e-3
        assert kf.measurement_variance == 1e-1
        assert kf.posteri_estimate == 0.0
        assert kf.posteri_error_estimate == 1.0
    
    def test_update(self):
        """Test Kalman filter update."""
        kf = KalmanFilter()
        
        # First measurement
        result1 = kf.update(10.0)
        assert result1 != 0.0  # Should have moved from initial 0
        
        # Second measurement
        result2 = kf.update(12.0)
        assert result2 != result1  # Should have updated
        
        # Filter should smooth values
        assert abs(result2 - 11.0) < 2.0  # Should be somewhere between measurements
    
    def test_convergence(self):
        """Test Kalman filter convergence."""
        kf = KalmanFilter()
        
        # Feed consistent measurements
        for _ in range(10):
            result = kf.update(50.0)
        
        # Should converge close to the measurement
        assert abs(result - 50.0) < 1.0


class TestWeightedAverageFilter:
    """Test WeightedAverageFilter class."""
    
    def test_initialization(self):
        """Test weighted average filter initialization."""
        waf = WeightedAverageFilter(window_size=5)
        
        assert waf.window_size == 5
        assert len(waf.readings) == 0
        assert len(waf.weights) == 0
    
    def test_update(self):
        """Test weighted average filter update."""
        waf = WeightedAverageFilter(window_size=3)
        
        result1 = waf.update(10.0, 1.0)
        assert result1 == 10.0  # First value
        
        result2 = waf.update(20.0, 1.0)
        assert result2 == 15.0  # Average of 10 and 20
        
        result3 = waf.update(30.0, 2.0)  # Higher weight
        expected = (10.0 * 1.0 + 20.0 * 1.0 + 30.0 * 2.0) / (1.0 + 1.0 + 2.0)
        assert abs(result3 - expected) < 0.001
    
    def test_window_limit(self):
        """Test window size limit."""
        waf = WeightedAverageFilter(window_size=2)
        
        waf.update(10.0, 1.0)
        waf.update(20.0, 1.0)
        waf.update(30.0, 1.0)  # Should push out first value
        
        assert len(waf.readings) == 2
        assert 10.0 not in waf.readings
        assert 20.0 in waf.readings
        assert 30.0 in waf.readings


class TestParticleFilter:
    """Test ParticleFilter class."""
    
    def test_initialization(self):
        """Test particle filter initialization."""
        pf = ParticleFilter(num_particles=50)
        
        assert pf.num_particles == 50
        assert len(pf.particles) == 50
        assert len(pf.weights) == 50
        assert abs(np.sum(pf.weights) - 1.0) < 1e-6  # Weights should sum to 1
    
    def test_update(self):
        """Test particle filter update."""
        pf = ParticleFilter(num_particles=100)
        
        # Update with measurement
        result1 = pf.update(10.0)
        result2 = pf.update(10.5)
        result3 = pf.update(9.8)
        
        # Results should be reasonable
        assert 8.0 < result1 < 12.0
        assert 8.0 < result2 < 12.0
        assert 8.0 < result3 < 12.0
    
    def test_resampling(self):
        """Test particle resampling."""
        pf = ParticleFilter(num_particles=10)
        
        # Create a situation that should trigger resampling
        # by making weights very uneven
        pf.weights = np.array([0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        result = pf.update(5.0)
        
        # After resampling, weights should be more uniform
        assert np.std(pf.weights) < 0.1


class TestSensorFusionManager:
    """Test SensorFusionManager class."""
    
    @pytest.fixture
    def fusion_manager(self, test_config):
        """Create fusion manager for testing."""
        return SensorFusionManager(test_config)
    
    def test_initialization(self, fusion_manager):
        """Test fusion manager initialization."""
        assert fusion_manager.is_running == False
        assert len(fusion_manager.sensors) == 0
        assert len(fusion_manager.fusion_algorithms) == 4
        
        # Check fusion algorithms are initialized
        assert 'kalman_filter' in fusion_manager.fusion_algorithms
        assert 'weighted_average' in fusion_manager.fusion_algorithms
        assert 'particle_filter' in fusion_manager.fusion_algorithms
        assert 'bayesian_fusion' in fusion_manager.fusion_algorithms
    
    @pytest.mark.asyncio
    async def test_initialize(self, fusion_manager):
        """Test fusion manager initialization."""
        with patch('psutil.disk_partitions', return_value=[]):
            await fusion_manager.initialize()
        
        # Should have initialized sensors
        assert len(fusion_manager.sensors) > 0
        assert len(fusion_manager.sensor_readings) == len(SensorType)
    
    @pytest.mark.asyncio
    async def test_start_shutdown(self, fusion_manager):
        """Test fusion manager start and shutdown."""
        with patch('psutil.disk_partitions', return_value=[]):
            await fusion_manager.initialize()
            await fusion_manager.start()
        
        assert fusion_manager.is_running == True
        assert len(fusion_manager.sensor_threads) > 0
        
        await fusion_manager.shutdown()
        
        assert fusion_manager.is_running == False
        assert len(fusion_manager.sensor_threads) == 0
    
    def test_read_cpu_sensor(self, fusion_manager):
        """Test CPU sensor reading."""
        with patch('psutil.cpu_percent', return_value=45.5):
            result = fusion_manager._read_cpu_sensor()
            assert result == 45.5
    
    def test_read_memory_sensor(self, fusion_manager):
        """Test memory sensor reading."""
        mock_memory = Mock()
        mock_memory.percent = 67.2
        
        with patch('psutil.virtual_memory', return_value=mock_memory):
            result = fusion_manager._read_memory_sensor()
            assert result == 67.2
    
    def test_read_disk_sensor(self, fusion_manager):
        """Test disk sensor reading."""
        mock_partition = Mock()
        mock_partition.mountpoint = "/"
        
        mock_usage = Mock()
        mock_usage.total = 1000
        mock_usage.used = 300
        
        with patch('psutil.disk_usage', return_value=mock_usage):
            result = fusion_manager._read_disk_sensor(mock_partition)
            assert result == 30.0  # 300/1000 * 100
    
    def test_read_network_sensor(self, fusion_manager):
        """Test network sensor reading."""
        mock_net_io1 = Mock()
        mock_net_io1.bytes_sent = 1000
        mock_net_io1.bytes_recv = 2000
        
        mock_net_io2 = Mock()
        mock_net_io2.bytes_sent = 1500
        mock_net_io2.bytes_recv = 2500
        
        with patch('psutil.net_io_counters', return_value=mock_net_io1):
            result1 = fusion_manager._read_network_sensor()
            assert result1 == 0.0  # First call returns 0
        
        with patch('psutil.net_io_counters', return_value=mock_net_io2):
            result2 = fusion_manager._read_network_sensor()
            assert result2 == 1000.0  # Difference: (1500-1000) + (2500-2000)
    
    def test_apply_calibration_disabled(self, fusion_manager):
        """Test calibration when disabled."""
        fusion_manager.config.sensors.calibration_enabled = False
        
        result = fusion_manager._apply_calibration("test_sensor", 50.0)
        assert result == 50.0
    
    def test_apply_calibration_enabled(self, fusion_manager):
        """Test calibration when enabled."""
        fusion_manager.config.sensors.calibration_enabled = True
        fusion_manager.calibration_data["test_sensor"] = {
            "offset": 5.0,
            "scale": 1.2
        }
        
        result = fusion_manager._apply_calibration("test_sensor", 50.0)
        assert result == (50.0 + 5.0) * 1.2  # (value + offset) * scale
    
    def test_assess_reading_quality_valid(self, fusion_manager):
        """Test quality assessment for valid readings."""
        fusion_manager.sensors["test_sensor"] = {
            'type': SensorType.CPU
        }
        
        quality = fusion_manager._assess_reading_quality("test_sensor", 45.5)
        assert quality == 1.0  # Valid CPU percentage
    
    def test_assess_reading_quality_invalid(self, fusion_manager):
        """Test quality assessment for invalid readings."""
        fusion_manager.sensors["test_sensor"] = {
            'type': SensorType.CPU
        }
        
        quality = fusion_manager._assess_reading_quality("test_sensor", 150.0)
        assert quality < 1.0  # Invalid CPU percentage
    
    def test_assess_reading_quality_outlier(self, fusion_manager):
        """Test quality assessment for outlier detection."""
        fusion_manager.sensors["test_sensor"] = {
            'type': SensorType.CPU
        }
        
        # Add some consistent readings
        sensor_readings = deque()
        for i in range(10):
            reading = SensorReading(
                sensor_id="test_sensor",
                sensor_type=SensorType.CPU,
                value=50.0,
                unit="percent",
                timestamp=time.time()
            )
            sensor_readings.append(reading)
        
        fusion_manager.sensor_readings[SensorType.CPU] = sensor_readings
        
        # Test outlier
        quality = fusion_manager._assess_reading_quality("test_sensor", 90.0)
        assert quality < 1.0  # Should detect as outlier
    
    @pytest.mark.asyncio
    async def test_kalman_fusion(self, fusion_manager):
        """Test Kalman filter fusion."""
        readings = [
            SensorReading("sensor1", SensorType.CPU, 45.0, "percent", time.time(), 1.0),
            SensorReading("sensor2", SensorType.CPU, 50.0, "percent", time.time(), 0.9),
        ]
        
        result = await fusion_manager._kalman_fusion(SensorType.CPU, readings)
        
        assert result is not None
        assert isinstance(result, FusedData)
        assert result.fusion_method == 'kalman_filter'
        assert result.confidence == 0.9
        assert len(result.contributing_sensors) == 2
    
    @pytest.mark.asyncio
    async def test_weighted_average_fusion(self, fusion_manager):
        """Test weighted average fusion."""
        readings = [
            SensorReading("sensor1", SensorType.CPU, 40.0, "percent", time.time(), 1.0),
            SensorReading("sensor2", SensorType.CPU, 60.0, "percent", time.time(), 0.8),
        ]
        
        result = await fusion_manager._weighted_average_fusion(SensorType.CPU, readings)
        
        assert result is not None
        assert isinstance(result, FusedData)
        assert result.fusion_method == 'weighted_average'
        # Weighted average: (40*1.0 + 60*0.8) / (1.0 + 0.8) = 88/1.8 ≈ 48.89
        assert abs(result.fused_value - 48.89) < 0.1
    
    @pytest.mark.asyncio
    async def test_particle_filter_fusion(self, fusion_manager):
        """Test particle filter fusion."""
        readings = [
            SensorReading("sensor1", SensorType.CPU, 45.0, "percent", time.time(), 0.9),
        ]
        
        result = await fusion_manager._particle_filter_fusion(SensorType.CPU, readings)
        
        assert result is not None
        assert isinstance(result, FusedData)
        assert result.fusion_method == 'particle_filter'
        assert result.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_simple_average_fusion(self, fusion_manager):
        """Test simple average fusion."""
        readings = [
            SensorReading("sensor1", SensorType.CPU, 40.0, "percent", time.time(), 1.0),
            SensorReading("sensor2", SensorType.CPU, 60.0, "percent", time.time(), 1.0),
        ]
        
        result = await fusion_manager._simple_average_fusion(SensorType.CPU, readings)
        
        assert result is not None
        assert isinstance(result, FusedData)
        assert result.fusion_method == 'simple_average'
        assert result.fused_value == 50.0  # (40 + 60) / 2
    
    @pytest.mark.asyncio
    async def test_sensor_reading_safe_success(self, fusion_manager):
        """Test safe sensor reading success."""
        def mock_read_function():
            return 42.0
        
        result = await fusion_manager._read_sensor_safe(mock_read_function)
        assert result == 42.0
    
    @pytest.mark.asyncio
    async def test_sensor_reading_safe_async(self, fusion_manager):
        """Test safe sensor reading with async function."""
        async def mock_async_read_function():
            return 42.0
        
        result = await fusion_manager._read_sensor_safe(mock_async_read_function)
        assert result == 42.0
    
    @pytest.mark.asyncio
    async def test_sensor_reading_safe_error(self, fusion_manager):
        """Test safe sensor reading with error."""
        def mock_failing_read_function():
            raise Exception("Sensor error")
        
        result = await fusion_manager._read_sensor_safe(mock_failing_read_function)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_load_save_calibration_data(self, fusion_manager, temp_dir):
        """Test calibration data loading and saving."""
        # Set up test calibration data
        test_calibration = {
            "sensor1": {"offset": 1.0, "scale": 1.1},
            "sensor2": {"offset": -0.5, "scale": 0.9}
        }
        
        fusion_manager.calibration_data = test_calibration
        
        # Test saving
        await fusion_manager._save_calibration_data()
        
        # Clear and test loading
        fusion_manager.calibration_data = {}
        await fusion_manager._load_calibration_data()
        
        # Should have loaded the data (or at least not crashed)
        # Note: Actual file I/O depends on implementation details


@pytest.mark.integration
class TestSensorFusionIntegration:
    """Integration tests for sensor fusion."""
    
    @pytest.mark.asyncio
    async def test_full_sensor_fusion_cycle(self, test_config):
        """Test complete sensor fusion lifecycle."""
        # Configure for limited sensors to avoid system dependencies
        test_config.sensors.enabled_sensors = ['cpu', 'memory']
        
        fusion_manager = SensorFusionManager(test_config)
        
        try:
            # Mock system calls to avoid dependencies
            with patch('psutil.cpu_percent', return_value=45.5), \
                 patch('psutil.virtual_memory') as mock_memory, \
                 patch('psutil.disk_partitions', return_value=[]):
                
                mock_memory.return_value.percent = 67.2
                
                await fusion_manager.initialize()
                await fusion_manager.start()
                
                # Let it run briefly
                await asyncio.sleep(0.2)
                
                # Check that sensor readings were collected
                assert len(fusion_manager.sensor_readings[SensorType.CPU]) > 0
                assert len(fusion_manager.sensor_readings[SensorType.MEMORY]) > 0
                
        finally:
            await fusion_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_fusion_algorithm_switching(self, test_config):
        """Test switching between different fusion algorithms."""
        fusion_manager = SensorFusionManager(test_config)
        
        # Test different fusion methods
        readings = [
            SensorReading("sensor1", SensorType.CPU, 40.0, "percent", time.time(), 1.0),
            SensorReading("sensor2", SensorType.CPU, 60.0, "percent", time.time(), 1.0),
        ]
        
        # Test Kalman filter
        test_config.sensors.fusion_algorithm = 'kalman_filter'
        result1 = await fusion_manager._kalman_fusion(SensorType.CPU, readings)
        assert result1.fusion_method == 'kalman_filter'
        
        # Test weighted average
        test_config.sensors.fusion_algorithm = 'weighted_average'
        result2 = await fusion_manager._weighted_average_fusion(SensorType.CPU, readings)
        assert result2.fusion_method == 'weighted_average'
        
        # Test particle filter
        test_config.sensors.fusion_algorithm = 'particle_filter'
        result3 = await fusion_manager._particle_filter_fusion(SensorType.CPU, readings)
        assert result3.fusion_method == 'particle_filter'
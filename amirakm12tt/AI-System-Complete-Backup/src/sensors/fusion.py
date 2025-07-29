"""
Sensor Fusion Manager
Advanced sensor data aggregation and fusion using multiple algorithms
"""

import asyncio
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import psutil
import threading
from collections import deque
import statistics

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class SensorType(Enum):
    """Types of sensors supported."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    TEMPERATURE = "temperature"
    POWER = "power"
    CUSTOM = "custom"

@dataclass
class SensorReading:
    """Individual sensor reading."""
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: float
    quality: float = 1.0  # Quality factor (0-1)
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FusedData:
    """Fused sensor data result."""
    sensor_types: List[SensorType]
    fused_value: float
    confidence: float
    timestamp: float
    contributing_sensors: List[str]
    fusion_method: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class KalmanFilter:
    """Kalman filter for sensor fusion."""
    
    def __init__(self, process_variance: float = 1e-3, measurement_variance: float = 1e-1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.posteri_estimate = 0.0
        self.posteri_error_estimate = 1.0
        
    def update(self, measurement: float) -> float:
        """Update filter with new measurement."""
        # Prediction step
        priori_estimate = self.posteri_estimate
        priori_error_estimate = self.posteri_error_estimate + self.process_variance
        
        # Update step
        blending_factor = priori_error_estimate / (priori_error_estimate + self.measurement_variance)
        self.posteri_estimate = priori_estimate + blending_factor * (measurement - priori_estimate)
        self.posteri_error_estimate = (1 - blending_factor) * priori_error_estimate
        
        return self.posteri_estimate

class WeightedAverageFilter:
    """Weighted average filter for sensor fusion."""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.readings = deque(maxlen=window_size)
        self.weights = deque(maxlen=window_size)
        
    def update(self, value: float, weight: float = 1.0) -> float:
        """Update filter with new weighted value."""
        self.readings.append(value)
        self.weights.append(weight)
        
        if len(self.readings) == 0:
            return 0.0
            
        weighted_sum = sum(r * w for r, w in zip(self.readings, self.weights))
        weight_sum = sum(self.weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0

class ParticleFilter:
    """Particle filter for non-linear sensor fusion."""
    
    def __init__(self, num_particles: int = 100):
        self.num_particles = num_particles
        self.particles = np.random.normal(0, 1, num_particles)
        self.weights = np.ones(num_particles) / num_particles
        
    def update(self, measurement: float, measurement_noise: float = 0.1) -> float:
        """Update particle filter with new measurement."""
        # Prediction step (random walk)
        self.particles += np.random.normal(0, 0.1, self.num_particles)
        
        # Update weights based on measurement likelihood
        likelihood = np.exp(-0.5 * ((self.particles - measurement) / measurement_noise) ** 2)
        self.weights *= likelihood
        self.weights /= np.sum(self.weights)
        
        # Resample if effective sample size is low
        effective_sample_size = 1.0 / np.sum(self.weights ** 2)
        if effective_sample_size < self.num_particles / 2:
            indices = np.random.choice(self.num_particles, self.num_particles, p=self.weights)
            self.particles = self.particles[indices]
            self.weights = np.ones(self.num_particles) / self.num_particles
        
        # Return weighted average
        return np.average(self.particles, weights=self.weights)

class SensorFusionManager:
    """Manages sensor data collection and fusion."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        
        # Sensor management
        self.sensors = {}
        self.sensor_readings = {}
        self.fusion_algorithms = {}
        self.fused_data_history = deque(maxlen=10000)
        
        # Threading for concurrent sensor reading
        self.sensor_threads = {}
        self.reading_lock = threading.Lock()
        
        # Fusion algorithms
        self._initialize_fusion_algorithms()
        
        # Sensor calibration data
        self.calibration_data = {}
        
        logger.info("Sensor Fusion Manager initialized")
    
    def _initialize_fusion_algorithms(self):
        """Initialize fusion algorithms."""
        self.fusion_algorithms = {
            'kalman_filter': {},
            'weighted_average': {},
            'particle_filter': {},
            'bayesian_fusion': {}
        }
        
        # Initialize filters for each sensor type
        for sensor_type in SensorType:
            self.fusion_algorithms['kalman_filter'][sensor_type] = KalmanFilter()
            self.fusion_algorithms['weighted_average'][sensor_type] = WeightedAverageFilter()
            self.fusion_algorithms['particle_filter'][sensor_type] = ParticleFilter()
    
    async def initialize(self):
        """Initialize sensor fusion system."""
        logger.info("Initializing Sensor Fusion Manager...")
        
        try:
            # Initialize sensors based on configuration
            await self._initialize_sensors()
            
            # Load calibration data
            await self._load_calibration_data()
            
            # Setup sensor reading buffers
            for sensor_type in SensorType:
                self.sensor_readings[sensor_type] = deque(maxlen=1000)
            
            logger.info("Sensor Fusion Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Sensor Fusion Manager: {e}")
            raise
    
    async def start(self):
        """Start sensor data collection and fusion."""
        logger.info("Starting Sensor Fusion Manager...")
        
        try:
            # Start sensor reading tasks
            for sensor_id, sensor_info in self.sensors.items():
                task = asyncio.create_task(self._sensor_reading_loop(sensor_id, sensor_info))
                self.sensor_threads[sensor_id] = task
            
            # Start fusion processing task
            self.sensor_threads['fusion_processor'] = asyncio.create_task(
                self._fusion_processing_loop()
            )
            
            # Start data validation task
            self.sensor_threads['data_validator'] = asyncio.create_task(
                self._data_validation_loop()
            )
            
            self.is_running = True
            logger.info("Sensor Fusion Manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Sensor Fusion Manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown sensor fusion system."""
        logger.info("Shutting down Sensor Fusion Manager...")
        
        self.is_running = False
        
        # Cancel all sensor tasks
        for task_name, task in self.sensor_threads.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled sensor task: {task_name}")
        
        self.sensor_threads.clear()
        
        # Save calibration data
        await self._save_calibration_data()
        
        logger.info("Sensor Fusion Manager shutdown complete")
    
    async def _initialize_sensors(self):
        """Initialize available sensors."""
        enabled_sensors = self.config.sensors.enabled_sensors
        
        # CPU sensor
        if 'cpu' in enabled_sensors:
            self.sensors['cpu_usage'] = {
                'type': SensorType.CPU,
                'name': 'CPU Usage',
                'unit': 'percent',
                'sampling_rate': self.config.sensors.sampling_rate,
                'read_function': self._read_cpu_sensor
            }
        
        # Memory sensor
        if 'memory' in enabled_sensors:
            self.sensors['memory_usage'] = {
                'type': SensorType.MEMORY,
                'name': 'Memory Usage',
                'unit': 'percent',
                'sampling_rate': self.config.sensors.sampling_rate,
                'read_function': self._read_memory_sensor
            }
        
        # Disk sensors
        if 'disk' in enabled_sensors:
            for i, partition in enumerate(psutil.disk_partitions()):
                sensor_id = f'disk_usage_{i}'
                self.sensors[sensor_id] = {
                    'type': SensorType.DISK,
                    'name': f'Disk Usage {partition.device}',
                    'unit': 'percent',
                    'sampling_rate': self.config.sensors.sampling_rate // 2,  # Less frequent
                    'read_function': lambda p=partition: self._read_disk_sensor(p),
                    'metadata': {'device': partition.device, 'mountpoint': partition.mountpoint}
                }
        
        # Network sensor
        if 'network' in enabled_sensors:
            self.sensors['network_usage'] = {
                'type': SensorType.NETWORK,
                'name': 'Network Usage',
                'unit': 'bytes/sec',
                'sampling_rate': self.config.sensors.sampling_rate,
                'read_function': self._read_network_sensor
            }
        
        # GPU sensor (if available)
        if 'gpu' in enabled_sensors:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    sensor_id = f'gpu_usage_{i}'
                    self.sensors[sensor_id] = {
                        'type': SensorType.GPU,
                        'name': f'GPU Usage {gpu.name}',
                        'unit': 'percent',
                        'sampling_rate': self.config.sensors.sampling_rate,
                        'read_function': lambda g=gpu: self._read_gpu_sensor(g),
                        'metadata': {'gpu_id': gpu.id, 'gpu_name': gpu.name}
                    }
            except ImportError:
                logger.warning("GPUtil not available, skipping GPU sensors")
        
        logger.info(f"Initialized {len(self.sensors)} sensors")
    
    async def _sensor_reading_loop(self, sensor_id: str, sensor_info: Dict[str, Any]):
        """Main sensor reading loop for a specific sensor."""
        sampling_interval = 1.0 / sensor_info['sampling_rate']
        
        while self.is_running:
            try:
                # Read sensor value
                raw_value = await self._read_sensor_safe(sensor_info['read_function'])
                
                if raw_value is not None:
                    # Apply calibration if available
                    calibrated_value = self._apply_calibration(sensor_id, raw_value)
                    
                    # Create sensor reading
                    reading = SensorReading(
                        sensor_id=sensor_id,
                        sensor_type=sensor_info['type'],
                        value=calibrated_value,
                        unit=sensor_info['unit'],
                        timestamp=time.time(),
                        quality=self._assess_reading_quality(sensor_id, calibrated_value),
                        metadata=sensor_info.get('metadata', {})
                    )
                    
                    # Store reading
                    with self.reading_lock:
                        self.sensor_readings[sensor_info['type']].append(reading)
                
                await asyncio.sleep(sampling_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading sensor {sensor_id}: {e}")
                await asyncio.sleep(sampling_interval)
    
    async def _read_sensor_safe(self, read_function) -> Optional[float]:
        """Safely read sensor value."""
        try:
            if asyncio.iscoroutinefunction(read_function):
                return await read_function()
            else:
                return read_function()
        except Exception as e:
            logger.error(f"Sensor read error: {e}")
            return None
    
    def _read_cpu_sensor(self) -> float:
        """Read CPU usage sensor."""
        return psutil.cpu_percent(interval=0.1)
    
    def _read_memory_sensor(self) -> float:
        """Read memory usage sensor."""
        return psutil.virtual_memory().percent
    
    def _read_disk_sensor(self, partition) -> float:
        """Read disk usage sensor."""
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            return (usage.used / usage.total) * 100
        except Exception:
            return 0.0
    
    def _read_network_sensor(self) -> float:
        """Read network usage sensor."""
        try:
            net_io = psutil.net_io_counters()
            if hasattr(self, '_last_net_io'):
                bytes_sent = net_io.bytes_sent - self._last_net_io.bytes_sent
                bytes_recv = net_io.bytes_recv - self._last_net_io.bytes_recv
                total_bytes = bytes_sent + bytes_recv
                self._last_net_io = net_io
                return total_bytes
            else:
                self._last_net_io = net_io
                return 0.0
        except Exception:
            return 0.0
    
    def _read_gpu_sensor(self, gpu) -> float:
        """Read GPU usage sensor."""
        try:
            gpu.load()  # Refresh GPU data
            return gpu.load * 100
        except Exception:
            return 0.0
    
    def _apply_calibration(self, sensor_id: str, raw_value: float) -> float:
        """Apply calibration to sensor reading."""
        if not self.config.sensors.calibration_enabled:
            return raw_value
        
        calibration = self.calibration_data.get(sensor_id, {})
        offset = calibration.get('offset', 0.0)
        scale = calibration.get('scale', 1.0)
        
        return (raw_value + offset) * scale
    
    def _assess_reading_quality(self, sensor_id: str, value: float) -> float:
        """Assess the quality of a sensor reading."""
        # Simple quality assessment based on value range and consistency
        quality = 1.0
        
        # Check for reasonable value ranges
        sensor_info = self.sensors.get(sensor_id, {})
        sensor_type = sensor_info.get('type')
        
        if sensor_type == SensorType.CPU and (value < 0 or value > 100):
            quality *= 0.5
        elif sensor_type == SensorType.MEMORY and (value < 0 or value > 100):
            quality *= 0.5
        elif sensor_type == SensorType.DISK and (value < 0 or value > 100):
            quality *= 0.5
        
        # Check for consistency with recent readings
        recent_readings = list(self.sensor_readings.get(sensor_type, []))[-10:]
        if len(recent_readings) > 3:
            recent_values = [r.value for r in recent_readings]
            mean_value = statistics.mean(recent_values)
            std_dev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0
            
            if std_dev > 0 and abs(value - mean_value) > 3 * std_dev:
                quality *= 0.7  # Outlier detection
        
        return max(0.0, min(1.0, quality))
    
    async def _fusion_processing_loop(self):
        """Main fusion processing loop."""
        while self.is_running:
            try:
                # Process fusion for each sensor type
                for sensor_type in SensorType:
                    if sensor_type in self.sensor_readings and self.sensor_readings[sensor_type]:
                        await self._process_sensor_fusion(sensor_type)
                
                await asyncio.sleep(1.0)  # Process fusion every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in fusion processing loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_sensor_fusion(self, sensor_type: SensorType):
        """Process sensor fusion for a specific sensor type."""
        readings = list(self.sensor_readings[sensor_type])
        
        if len(readings) < 2:
            return
        
        # Get recent readings (last 10 seconds)
        current_time = time.time()
        recent_readings = [
            r for r in readings
            if current_time - r.timestamp <= 10.0
        ]
        
        if not recent_readings:
            return
        
        # Apply configured fusion algorithm
        fusion_method = self.config.sensors.fusion_algorithm
        
        if fusion_method == 'kalman_filter':
            fused_result = await self._kalman_fusion(sensor_type, recent_readings)
        elif fusion_method == 'weighted_average':
            fused_result = await self._weighted_average_fusion(sensor_type, recent_readings)
        elif fusion_method == 'particle_filter':
            fused_result = await self._particle_filter_fusion(sensor_type, recent_readings)
        elif fusion_method == 'bayesian_fusion':
            fused_result = await self._bayesian_fusion(sensor_type, recent_readings)
        else:
            fused_result = await self._simple_average_fusion(sensor_type, recent_readings)
        
        if fused_result:
            self.fused_data_history.append(fused_result)
    
    async def _kalman_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply Kalman filter fusion."""
        if not readings:
            return None
        
        kalman_filter = self.fusion_algorithms['kalman_filter'][sensor_type]
        
        # Use the most recent reading for update
        latest_reading = max(readings, key=lambda r: r.timestamp)
        fused_value = kalman_filter.update(latest_reading.value)
        
        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=0.9,  # Kalman filter generally provides good confidence
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='kalman_filter'
        )
    
    async def _weighted_average_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply weighted average fusion."""
        if not readings:
            return None
        
        weighted_filter = self.fusion_algorithms['weighted_average'][sensor_type]
        
        # Calculate weighted average based on reading quality
        total_weight = sum(r.quality for r in readings)
        if total_weight == 0:
            return None
        
        weighted_sum = sum(r.value * r.quality for r in readings)
        fused_value = weighted_sum / total_weight
        
        # Update filter
        weighted_filter.update(fused_value, total_weight / len(readings))
        
        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=min(1.0, total_weight / len(readings)),
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='weighted_average'
        )
    
    async def _particle_filter_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply particle filter fusion."""
        if not readings:
            return None
        
        particle_filter = self.fusion_algorithms['particle_filter'][sensor_type]
        
        # Use the most recent high-quality reading
        quality_readings = [r for r in readings if r.quality > 0.5]
        if not quality_readings:
            return None
        
        latest_reading = max(quality_readings, key=lambda r: r.timestamp)
        fused_value = particle_filter.update(latest_reading.value, 1.0 - latest_reading.quality)
        
        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=latest_reading.quality,
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='particle_filter'
        )
    
    async def _bayesian_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply Bayesian fusion."""
        if not readings:
            return None
        
        # Simple Bayesian fusion using weighted average with uncertainty
        weights = []
        values = []
        
        for reading in readings:
            # Weight inversely proportional to uncertainty (1 - quality)
            uncertainty = 1.0 - reading.quality
            weight = 1.0 / (uncertainty + 0.01)  # Add small epsilon to avoid division by zero
            weights.append(weight)
            values.append(reading.value)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        fused_value = sum(v * w for v, w in zip(values, weights)) / total_weight
        confidence = total_weight / (total_weight + len(readings))
        
        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=confidence,
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='bayesian_fusion'
        )
    
    async def _simple_average_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply simple average fusion as fallback."""
        if not readings:
            return None
        
        values = [r.value for r in readings]
        fused_value = statistics.mean(values)
        confidence = min(r.quality for r in readings)
        
        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=confidence,
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='simple_average'
        )
    
    async def _data_validation_loop(self):
        """Validate sensor data and detect anomalies."""
        while self.is_running:
            try:
                # Validate recent fused data
                recent_data = list(self.fused_data_history)[-100:]  # Last 100 readings
                
                for data in recent_data:
                    if self._detect_anomaly(data):
                        logger.warning(f"Anomaly detected in {data.sensor_types}: {data.fused_value}")
                
                await asyncio.sleep(30)  # Validate every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data validation loop: {e}")
                await asyncio.sleep(30)
    
    def _detect_anomaly(self, fused_data: FusedData) -> bool:
        """Detect anomalies in fused data."""
        # Simple anomaly detection based on statistical analysis
        sensor_type = fused_data.sensor_types[0] if fused_data.sensor_types else None
        
        if not sensor_type:
            return False
        
        # Get historical data for the same sensor type
        historical_data = [
            d for d in self.fused_data_history
            if sensor_type in d.sensor_types and d.timestamp < fused_data.timestamp
        ]
        
        if len(historical_data) < 10:
            return False
        
        # Calculate statistical thresholds
        values = [d.fused_value for d in historical_data[-50:]]  # Last 50 readings
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Detect outliers (beyond 3 standard deviations)
        if std_dev > 0:
            z_score = abs(fused_data.fused_value - mean_value) / std_dev
            return z_score > 3.0
        
        return False
    
    async def _load_calibration_data(self):
        """Load sensor calibration data."""
        try:
            calibration_file = self.config.data_dir / "sensor_calibration.json"
            if calibration_file.exists():
                with open(calibration_file, 'r') as f:
                    self.calibration_data = json.load(f)
                logger.info("Loaded sensor calibration data")
        except Exception as e:
            logger.error(f"Error loading calibration data: {e}")
    
    async def _save_calibration_data(self):
        """Save sensor calibration data."""
        try:
            calibration_file = self.config.data_dir / "sensor_calibration.json"
            with open(calibration_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            logger.info("Saved sensor calibration data")
        except Exception as e:
            logger.error(f"Error saving calibration data: {e}")
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            active_sensors = sum(1 for task in self.sensor_threads.values() if not task.done())
            total_sensors = len(self.sensor_threads)
            
            if active_sensors == total_sensors:
                return "healthy"
            elif active_sensors > total_sensors * 0.7:
                return "degraded"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """Get status of all sensors."""
        status = {}
        
        for sensor_id, sensor_info in self.sensors.items():
            recent_readings = [
                r for r in self.sensor_readings.get(sensor_info['type'], [])
                if r.sensor_id == sensor_id and time.time() - r.timestamp <= 60
            ]
            
            status[sensor_id] = {
                'type': sensor_info['type'].value,
                'name': sensor_info['name'],
                'unit': sensor_info['unit'],
                'recent_readings': len(recent_readings),
                'last_reading': recent_readings[-1].value if recent_readings else None,
                'average_quality': statistics.mean([r.quality for r in recent_readings]) if recent_readings else 0.0,
                'is_active': sensor_id in self.sensor_threads and not self.sensor_threads[sensor_id].done()
            }
        
        return status
    
    def get_fused_data(self, sensor_type: SensorType = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent fused data."""
        data = list(self.fused_data_history)
        
        if sensor_type:
            data = [d for d in data if sensor_type in d.sensor_types]
        
        # Return most recent data
        data = data[-limit:] if len(data) > limit else data
        
        return [
            {
                'sensor_types': [st.value for st in d.sensor_types],
                'fused_value': d.fused_value,
                'confidence': d.confidence,
                'timestamp': d.timestamp,
                'contributing_sensors': d.contributing_sensors,
                'fusion_method': d.fusion_method,
                'metadata': d.metadata
            }
            for d in data
        ]
    
    def calibrate_sensor(self, sensor_id: str, reference_value: float, measured_value: float):
        """Calibrate a sensor using reference measurement."""
        if sensor_id not in self.sensors:
            raise ValueError(f"Unknown sensor: {sensor_id}")
        
        # Calculate calibration parameters
        if sensor_id not in self.calibration_data:
            self.calibration_data[sensor_id] = {'offset': 0.0, 'scale': 1.0}
        
        # Simple linear calibration
        offset = reference_value - measured_value
        self.calibration_data[sensor_id]['offset'] = offset
        
        logger.info(f"Calibrated sensor {sensor_id}: offset={offset}")
    
    async def restart(self):
        """Restart the sensor fusion manager."""
        logger.info("Restarting Sensor Fusion Manager...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()

    async def _bayesian_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply Bayesian fusion."""
        if not readings:
            return None

        # Simple Bayesian fusion using weighted average with uncertainty
        weights = []
        values = []

        for reading in readings:
            # Weight inversely proportional to uncertainty (1 - quality)
            uncertainty = 1.0 - reading.quality
            weight = 1.0 / (uncertainty + 0.01)  # Add small epsilon to avoid division by zero
            weights.append(weight)
            values.append(reading.value)

        total_weight = sum(weights)
        if total_weight == 0:
            return None

        # Weighted average
        fused_value = sum(v * w for v, w in zip(values, weights)) / total_weight
        
        # Confidence based on weight distribution
        weight_variance = sum((w - total_weight/len(weights))**2 for w in weights) / len(weights)
        confidence = max(0.1, min(1.0, 1.0 - weight_variance / (total_weight/len(weights))**2))

        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=confidence,
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='bayesian_fusion'
        )

    async def _simple_average_fusion(self, sensor_type: SensorType, readings: List[SensorReading]) -> Optional[FusedData]:
        """Apply simple average fusion as fallback."""
        if not readings:
            return None

        # Simple arithmetic mean
        values = [r.value for r in readings]
        fused_value = sum(values) / len(values)
        
        # Confidence based on quality average
        avg_quality = sum(r.quality for r in readings) / len(readings)

        return FusedData(
            sensor_types=[sensor_type],
            fused_value=fused_value,
            confidence=avg_quality,
            timestamp=time.time(),
            contributing_sensors=[r.sensor_id for r in readings],
            fusion_method='simple_average'
        )

    async def _load_calibration_data(self):
        """Load sensor calibration data from file."""
        calibration_file = self.config.data_dir / "sensor_calibration.json"
        
        if calibration_file.exists():
            try:
                with open(calibration_file, 'r') as f:
                    self.calibration_data = json.load(f)
                logger.info(f"Loaded calibration data for {len(self.calibration_data)} sensors")
            except Exception as e:
                logger.error(f"Error loading calibration data: {e}")
                self.calibration_data = {}
        else:
            self.calibration_data = {}

    async def _save_calibration_data(self):
        """Save sensor calibration data to file."""
        calibration_file = self.config.data_dir / "sensor_calibration.json"
        
        try:
            with open(calibration_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            logger.info(f"Saved calibration data for {len(self.calibration_data)} sensors")
        except Exception as e:
            logger.error(f"Error saving calibration data: {e}")

    async def _data_validation_loop(self):
        """Validate fused data for anomalies."""
        while self.is_running:
            try:
                if len(self.fused_data_history) > 10:
                    # Get recent fused data
                    recent_data = list(self.fused_data_history)[-10:]
                    
                    # Check for anomalies in each sensor type
                    for sensor_type in SensorType:
                        type_data = [d for d in recent_data if sensor_type in d.sensor_types]
                        
                        if len(type_data) > 3:
                            values = [d.fused_value for d in type_data]
                            mean_val = statistics.mean(values)
                            std_val = statistics.stdev(values) if len(values) > 1 else 0
                            
                            # Check latest value for anomaly
                            latest_val = type_data[-1].fused_value
                            if std_val > 0 and abs(latest_val - mean_val) > 3 * std_val:
                                logger.warning(f"Anomaly detected in {sensor_type.value}: {latest_val} (mean: {mean_val:.2f}, std: {std_val:.2f})")

                await asyncio.sleep(5)  # Check every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data validation loop: {e}")
                await asyncio.sleep(1)

    def get_sensor_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sensor statistics."""
        stats = {
            'total_sensors': len(self.sensors),
            'active_sensors': sum(1 for s in self.sensors.values() if s.get('active', True)),
            'fusion_algorithm': self.config.sensors.fusion_algorithm,
            'sampling_rate': self.config.sensors.sampling_rate,
            'total_readings': sum(len(readings) for readings in self.sensor_readings.values()),
            'fused_data_points': len(self.fused_data_history),
            'sensor_types': {}
        }

        # Per-sensor-type statistics
        for sensor_type in SensorType:
            readings = self.sensor_readings.get(sensor_type, [])
            if readings:
                values = [r.value for r in readings]
                qualities = [r.quality for r in readings]
                
                stats['sensor_types'][sensor_type.value] = {
                    'reading_count': len(readings),
                    'avg_value': statistics.mean(values) if values else 0,
                    'avg_quality': statistics.mean(qualities) if qualities else 0,
                    'latest_reading': readings[-1].timestamp if readings else None
                }

        return stats

    async def health_check(self) -> str:
        """Perform health check on sensor fusion system."""
        try:
            if not self.is_running:
                return "unhealthy"

            # Check if sensors are producing data
            active_sensors = 0
            for sensor_type, readings in self.sensor_readings.items():
                if readings and time.time() - readings[-1].timestamp < 30:  # Recent reading within 30 seconds
                    active_sensors += 1

            if active_sensors == 0:
                return "unhealthy"
            elif active_sensors < len(self.sensor_readings) / 2:
                return "degraded"
            else:
                return "healthy"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
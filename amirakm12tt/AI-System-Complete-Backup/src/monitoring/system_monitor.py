"""
System Monitor
Comprehensive system monitoring and performance tracking
"""

import asyncio
import logging
import time
import psutil
import platform
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from collections import deque, defaultdict
import statistics

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class SystemMetric:
    """System metric data point."""
    name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """System alert."""
    alert_id: str
    level: AlertLevel
    message: str
    metric_name: str
    threshold: float
    current_value: float
    timestamp: float
    acknowledged: bool
    metadata: Dict[str, Any]

class SystemMonitor:
    """Comprehensive system monitoring service."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        
        # Metrics storage
        self.metrics_history = defaultdict(lambda: deque(maxlen=10000))
        self.current_metrics = {}
        
        # Alert management
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_thresholds = self.config.monitoring.alert_thresholds.copy()
        
        # System information
        self.system_info = {}
        self.baseline_metrics = {}
        
        # Performance tracking
        self.performance_stats = {
            'uptime': 0.0,
            'total_alerts': 0,
            'critical_alerts': 0,
            'monitoring_cycles': 0,
            'average_cycle_time': 0.0
        }
        
        logger.info("System Monitor initialized")
    
    async def initialize(self):
        """Initialize the system monitor."""
        logger.info("Initializing System Monitor...")
        
        try:
            # Gather initial system information
            await self._gather_system_info()
            
            # Establish baseline metrics
            await self._establish_baseline()
            
            # Initialize monitoring components
            await self._initialize_monitoring()
            
            logger.info("System Monitor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize System Monitor: {e}")
            raise
    
    async def start(self):
        """Start the system monitor."""
        logger.info("Starting System Monitor...")
        
        try:
            # Start monitoring tasks
            self.monitoring_tasks = {
                'system_metrics': asyncio.create_task(self._system_metrics_loop()),
                'process_monitor': asyncio.create_task(self._process_monitoring_loop()),
                'disk_monitor': asyncio.create_task(self._disk_monitoring_loop()),
                'network_monitor': asyncio.create_task(self._network_monitoring_loop()),
                'alert_processor': asyncio.create_task(self._alert_processing_loop()),
                'performance_tracker': asyncio.create_task(self._performance_tracking_loop()),
                'cleanup_manager': asyncio.create_task(self._cleanup_management_loop())
            }
            
            self.is_running = True
            self.start_time = time.time()
            
            logger.info("System Monitor started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start System Monitor: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the system monitor."""
        logger.info("Shutting down System Monitor...")
        
        self.is_running = False
        
        # Cancel monitoring tasks
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Save metrics and alerts
        await self._save_monitoring_data()
        
        logger.info("System Monitor shutdown complete")
    
    async def _gather_system_info(self):
        """Gather comprehensive system information."""
        self.system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'boot_time': psutil.boot_time(),
            'python_version': platform.python_version()
        }
        
        # Get disk information
        self.system_info['disks'] = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.system_info['disks'].append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free
                })
            except Exception as e:
                logger.warning(f"Could not get disk usage for {partition.device}: {e}")
        
        # Get network interfaces
        self.system_info['network_interfaces'] = {}
        for interface, addresses in psutil.net_if_addrs().items():
            self.system_info['network_interfaces'][interface] = []
            for addr in addresses:
                self.system_info['network_interfaces'][interface].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
    
    async def _establish_baseline(self):
        """Establish baseline metrics for comparison."""
        logger.info("Establishing baseline metrics...")
        
        # Collect baseline samples
        baseline_samples = []
        for _ in range(10):
            sample = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_io': psutil.disk_io_counters(),
                'network_io': psutil.net_io_counters()
            }
            baseline_samples.append(sample)
            await asyncio.sleep(0.5)
        
        # Calculate baseline averages
        self.baseline_metrics = {
            'cpu_percent': statistics.mean([s['cpu_percent'] for s in baseline_samples]),
            'memory_percent': statistics.mean([s['memory_percent'] for s in baseline_samples]),
            'established_at': time.time()
        }
        
        logger.info(f"Baseline established - CPU: {self.baseline_metrics['cpu_percent']:.1f}%, "
                   f"Memory: {self.baseline_metrics['memory_percent']:.1f}%")
    
    async def _initialize_monitoring(self):
        """Initialize monitoring components."""
        # Set up metric collectors
        self.metric_collectors = {
            'cpu': self._collect_cpu_metrics,
            'memory': self._collect_memory_metrics,
            'disk': self._collect_disk_metrics,
            'network': self._collect_network_metrics,
            'processes': self._collect_process_metrics,
            'system': self._collect_system_metrics
        }
    
    async def _system_metrics_loop(self):
        """Main system metrics collection loop."""
        while self.is_running:
            try:
                cycle_start = time.time()
                
                # Collect all metrics
                for metric_type, collector in self.metric_collectors.items():
                    try:
                        metrics = await collector()
                        for metric in metrics:
                            self._store_metric(metric)
                            self._check_thresholds(metric)
                    except Exception as e:
                        logger.error(f"Error collecting {metric_type} metrics: {e}")
                
                # Update performance stats
                cycle_time = time.time() - cycle_start
                self.performance_stats['monitoring_cycles'] += 1
                total_cycles = self.performance_stats['monitoring_cycles']
                
                if total_cycles > 1:
                    self.performance_stats['average_cycle_time'] = (
                        (self.performance_stats['average_cycle_time'] * (total_cycles - 1) + cycle_time) / total_cycles
                    )
                else:
                    self.performance_stats['average_cycle_time'] = cycle_time
                
                # Sleep until next collection
                await asyncio.sleep(max(0.1, 1.0 - cycle_time))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system metrics loop: {e}")
                await asyncio.sleep(1)
    
    async def _collect_cpu_metrics(self) -> List[SystemMetric]:
        """Collect CPU metrics."""
        metrics = []
        
        # Overall CPU usage
        cpu_percent = psutil.cpu_percent(interval=0)
        metrics.append(SystemMetric(
            name='cpu_usage_percent',
            value=cpu_percent,
            unit='percent',
            timestamp=time.time(),
            metadata={'type': 'overall'}
        ))
        
        # Per-CPU usage
        cpu_percents = psutil.cpu_percent(percpu=True, interval=0)
        for i, cpu_pct in enumerate(cpu_percents):
            metrics.append(SystemMetric(
                name=f'cpu_usage_percent_core_{i}',
                value=cpu_pct,
                unit='percent',
                timestamp=time.time(),
                metadata={'type': 'per_core', 'core': i}
            ))
        
        # CPU frequency
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                metrics.append(SystemMetric(
                    name='cpu_frequency_mhz',
                    value=cpu_freq.current,
                    unit='MHz',
                    timestamp=time.time(),
                    metadata={'max': cpu_freq.max, 'min': cpu_freq.min}
                ))
        except Exception:
            pass
        
        # Load average (Unix-like systems)
        try:
            load_avg = psutil.getloadavg()
            for i, load in enumerate(load_avg):
                metrics.append(SystemMetric(
                    name=f'load_average_{[1, 5, 15][i]}min',
                    value=load,
                    unit='load',
                    timestamp=time.time(),
                    metadata={'period': f'{[1, 5, 15][i]} minutes'}
                ))
        except Exception:
            pass
        
        return metrics
    
    async def _collect_memory_metrics(self) -> List[SystemMetric]:
        """Collect memory metrics."""
        metrics = []
        
        # Virtual memory
        vmem = psutil.virtual_memory()
        metrics.extend([
            SystemMetric('memory_total_bytes', vmem.total, 'bytes', time.time(), {'type': 'virtual'}),
            SystemMetric('memory_available_bytes', vmem.available, 'bytes', time.time(), {'type': 'virtual'}),
            SystemMetric('memory_used_bytes', vmem.used, 'bytes', time.time(), {'type': 'virtual'}),
            SystemMetric('memory_free_bytes', vmem.free, 'bytes', time.time(), {'type': 'virtual'}),
            SystemMetric('memory_usage_percent', vmem.percent, 'percent', time.time(), {'type': 'virtual'})
        ])
        
        # Swap memory
        swap = psutil.swap_memory()
        metrics.extend([
            SystemMetric('swap_total_bytes', swap.total, 'bytes', time.time(), {'type': 'swap'}),
            SystemMetric('swap_used_bytes', swap.used, 'bytes', time.time(), {'type': 'swap'}),
            SystemMetric('swap_free_bytes', swap.free, 'bytes', time.time(), {'type': 'swap'}),
            SystemMetric('swap_usage_percent', swap.percent, 'percent', time.time(), {'type': 'swap'})
        ])
        
        return metrics
    
    async def _collect_disk_metrics(self) -> List[SystemMetric]:
        """Collect disk metrics."""
        metrics = []
        
        # Disk usage per partition
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                device_name = partition.device.replace('/', '_').replace('\\', '_')
                
                metrics.extend([
                    SystemMetric(f'disk_total_bytes_{device_name}', usage.total, 'bytes', time.time(), 
                               {'device': partition.device, 'mountpoint': partition.mountpoint}),
                    SystemMetric(f'disk_used_bytes_{device_name}', usage.used, 'bytes', time.time(),
                               {'device': partition.device, 'mountpoint': partition.mountpoint}),
                    SystemMetric(f'disk_free_bytes_{device_name}', usage.free, 'bytes', time.time(),
                               {'device': partition.device, 'mountpoint': partition.mountpoint}),
                    SystemMetric(f'disk_usage_percent_{device_name}', 
                               (usage.used / usage.total) * 100, 'percent', time.time(),
                               {'device': partition.device, 'mountpoint': partition.mountpoint})
                ])
            except Exception as e:
                logger.warning(f"Could not collect disk metrics for {partition.device}: {e}")
        
        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.extend([
                    SystemMetric('disk_read_bytes_total', disk_io.read_bytes, 'bytes', time.time(), {'type': 'io'}),
                    SystemMetric('disk_write_bytes_total', disk_io.write_bytes, 'bytes', time.time(), {'type': 'io'}),
                    SystemMetric('disk_read_count_total', disk_io.read_count, 'count', time.time(), {'type': 'io'}),
                    SystemMetric('disk_write_count_total', disk_io.write_count, 'count', time.time(), {'type': 'io'})
                ])
        except Exception:
            pass
        
        return metrics
    
    async def _collect_network_metrics(self) -> List[SystemMetric]:
        """Collect network metrics."""
        metrics = []
        
        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                metrics.extend([
                    SystemMetric('network_bytes_sent_total', net_io.bytes_sent, 'bytes', time.time(), {'type': 'io'}),
                    SystemMetric('network_bytes_recv_total', net_io.bytes_recv, 'bytes', time.time(), {'type': 'io'}),
                    SystemMetric('network_packets_sent_total', net_io.packets_sent, 'packets', time.time(), {'type': 'io'}),
                    SystemMetric('network_packets_recv_total', net_io.packets_recv, 'packets', time.time(), {'type': 'io'}),
                    SystemMetric('network_errors_in_total', net_io.errin, 'errors', time.time(), {'type': 'io'}),
                    SystemMetric('network_errors_out_total', net_io.errout, 'errors', time.time(), {'type': 'io'})
                ])
        except Exception:
            pass
        
        # Per-interface metrics
        try:
            net_io_per_if = psutil.net_io_counters(pernic=True)
            for interface, io_counters in net_io_per_if.items():
                interface_clean = interface.replace(' ', '_').replace('-', '_')
                metrics.extend([
                    SystemMetric(f'network_bytes_sent_{interface_clean}', io_counters.bytes_sent, 'bytes', 
                               time.time(), {'interface': interface}),
                    SystemMetric(f'network_bytes_recv_{interface_clean}', io_counters.bytes_recv, 'bytes',
                               time.time(), {'interface': interface})
                ])
        except Exception:
            pass
        
        return metrics
    
    async def _collect_process_metrics(self) -> List[SystemMetric]:
        """Collect process metrics."""
        metrics = []
        
        # Process count
        process_count = len(psutil.pids())
        metrics.append(SystemMetric(
            'process_count_total', process_count, 'count', time.time(), {'type': 'processes'}
        ))
        
        # Top processes by CPU and memory
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            top_cpu_processes = processes[:5]
            
            for i, proc in enumerate(top_cpu_processes):
                metrics.append(SystemMetric(
                    f'top_cpu_process_{i}_percent', proc.get('cpu_percent', 0), 'percent',
                    time.time(), {'pid': proc.get('pid'), 'name': proc.get('name')}
                ))
            
            # Sort by memory usage
            processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            top_mem_processes = processes[:5]
            
            for i, proc in enumerate(top_mem_processes):
                metrics.append(SystemMetric(
                    f'top_memory_process_{i}_percent', proc.get('memory_percent', 0), 'percent',
                    time.time(), {'pid': proc.get('pid'), 'name': proc.get('name')}
                ))
                
        except Exception as e:
            logger.warning(f"Error collecting top process metrics: {e}")
        
        return metrics
    
    async def _collect_system_metrics(self) -> List[SystemMetric]:
        """Collect general system metrics."""
        metrics = []
        
        # Uptime
        uptime = time.time() - psutil.boot_time()
        metrics.append(SystemMetric('system_uptime_seconds', uptime, 'seconds', time.time(), {'type': 'system'}))
        
        # Users
        try:
            user_count = len(psutil.users())
            metrics.append(SystemMetric('system_users_count', user_count, 'count', time.time(), {'type': 'system'}))
        except Exception:
            pass
        
        return metrics
    
    def _store_metric(self, metric: SystemMetric):
        """Store a metric in history and update current values."""
        self.metrics_history[metric.name].append(metric)
        self.current_metrics[metric.name] = metric
    
    def _check_thresholds(self, metric: SystemMetric):
        """Check if metric exceeds thresholds and generate alerts."""
        # Map metric names to threshold keys
        threshold_mapping = {
            'cpu_usage_percent': 'cpu_usage',
            'memory_usage_percent': 'memory_usage',
            'disk_usage_percent': 'disk_usage'
        }
        
        # Check for disk usage thresholds
        for disk_metric in self.current_metrics:
            if disk_metric.startswith('disk_usage_percent_'):
                threshold_key = 'disk_usage'
                if threshold_key in self.alert_thresholds:
                    threshold = self.alert_thresholds[threshold_key]
                    if metric.name == disk_metric and metric.value > threshold:
                        self._generate_alert(metric, threshold, AlertLevel.WARNING)
        
        # Check other thresholds
        for metric_pattern, threshold_key in threshold_mapping.items():
            if metric.name.startswith(metric_pattern) and threshold_key in self.alert_thresholds:
                threshold = self.alert_thresholds[threshold_key]
                
                if metric.value > threshold:
                    # Determine alert level based on how much threshold is exceeded
                    if metric.value > threshold * 1.5:
                        level = AlertLevel.CRITICAL
                    elif metric.value > threshold * 1.2:
                        level = AlertLevel.ERROR
                    else:
                        level = AlertLevel.WARNING
                    
                    self._generate_alert(metric, threshold, level)
    
    def _generate_alert(self, metric: SystemMetric, threshold: float, level: AlertLevel):
        """Generate an alert for a metric threshold violation."""
        alert_id = f"{metric.name}_{level.value}_{int(time.time())}"
        
        # Check if similar alert already exists
        existing_alert = None
        for alert in self.active_alerts.values():
            if (alert.metric_name == metric.name and 
                alert.level == level and 
                not alert.acknowledged and
                time.time() - alert.timestamp < 300):  # 5 minutes
                existing_alert = alert
                break
        
        if existing_alert:
            # Update existing alert
            existing_alert.current_value = metric.value
            existing_alert.timestamp = time.time()
        else:
            # Create new alert
            alert = Alert(
                alert_id=alert_id,
                level=level,
                message=f"{metric.name} ({metric.value:.2f}{metric.unit}) exceeded threshold ({threshold:.2f}{metric.unit})",
                metric_name=metric.name,
                threshold=threshold,
                current_value=metric.value,
                timestamp=time.time(),
                acknowledged=False,
                metadata=metric.metadata.copy()
            )
            
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.performance_stats['total_alerts'] += 1
            
            if level == AlertLevel.CRITICAL:
                self.performance_stats['critical_alerts'] += 1
            
            logger.warning(f"Generated {level.value} alert: {alert.message}")
    
    async def _process_monitoring_loop(self):
        """Monitor system processes."""
        while self.is_running:
            try:
                # This could be expanded to monitor specific processes
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _disk_monitoring_loop(self):
        """Monitor disk health and usage."""
        while self.is_running:
            try:
                # Monitor disk health (could be expanded with SMART data)
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in disk monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _network_monitoring_loop(self):
        """Monitor network connectivity and performance."""
        while self.is_running:
            try:
                # Monitor network connectivity
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in network monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _alert_processing_loop(self):
        """Process and manage alerts."""
        while self.is_running:
            try:
                current_time = time.time()
                
                # Auto-acknowledge old alerts
                for alert_id, alert in list(self.active_alerts.items()):
                    if current_time - alert.timestamp > 3600:  # 1 hour
                        alert.acknowledged = True
                        logger.info(f"Auto-acknowledged old alert: {alert_id}")
                
                # Clean up acknowledged alerts
                acknowledged_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.acknowledged and current_time - alert.timestamp > 1800  # 30 minutes
                ]
                
                for alert_id in acknowledged_alerts:
                    del self.active_alerts[alert_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60)
    
    async def _performance_tracking_loop(self):
        """Track system monitor performance."""
        while self.is_running:
            try:
                if hasattr(self, 'start_time'):
                    self.performance_stats['uptime'] = time.time() - self.start_time
                
                # Log performance stats
                logger.info(f"System Monitor Performance - "
                          f"Uptime: {self.performance_stats['uptime']:.1f}s, "
                          f"Cycles: {self.performance_stats['monitoring_cycles']}, "
                          f"Avg Cycle Time: {self.performance_stats['average_cycle_time']:.3f}s, "
                          f"Active Alerts: {len(self.active_alerts)}")
                
                await asyncio.sleep(300)  # Log every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance tracking loop: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_management_loop(self):
        """Manage cleanup of old metrics and alerts."""
        while self.is_running:
            try:
                current_time = time.time()
                max_age = 86400  # 24 hours
                
                # Clean up old metrics
                for metric_name, history in self.metrics_history.items():
                    # Convert deque to list for filtering
                    recent_metrics = [m for m in history if current_time - m.timestamp <= max_age]
                    
                    # Clear and repopulate with recent metrics
                    history.clear()
                    history.extend(recent_metrics)
                
                logger.info("Cleaned up old metrics data")
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup management: {e}")
                await asyncio.sleep(3600)
    
    async def _save_monitoring_data(self):
        """Save monitoring data to persistent storage."""
        # Placeholder for saving monitoring data
        pass
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Check if monitoring is running
            if not self.is_running:
                return "unhealthy"
            
            # Check if recent metrics exist
            recent_metrics = [
                m for m in self.current_metrics.values()
                if time.time() - m.timestamp <= 60
            ]
            
            if len(recent_metrics) > 0:
                return "healthy"
            else:
                return "degraded"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    async def perform_health_check(self):
        """Perform comprehensive health check."""
        return await self.health_check()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        current_time = time.time()
        
        # Get latest metrics
        latest_metrics = {}
        for name, metric in self.current_metrics.items():
            if current_time - metric.timestamp <= 60:  # Recent metrics only
                latest_metrics[name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp
                }
        
        # System summary
        system_summary = {
            'cpu_usage': latest_metrics.get('cpu_usage_percent', {}).get('value', 0),
            'memory_usage': latest_metrics.get('memory_usage_percent', {}).get('value', 0),
            'disk_usage': 0,  # Will be calculated from disk metrics
            'uptime': latest_metrics.get('system_uptime_seconds', {}).get('value', 0),
            'process_count': latest_metrics.get('process_count_total', {}).get('value', 0)
        }
        
        # Calculate average disk usage
        disk_usage_metrics = [m for m in latest_metrics.keys() if m.startswith('disk_usage_percent_')]
        if disk_usage_metrics:
            disk_usages = [latest_metrics[m]['value'] for m in disk_usage_metrics]
            system_summary['disk_usage'] = statistics.mean(disk_usages)
        
        return {
            'system_info': self.system_info,
            'current_metrics': latest_metrics,
            'system_summary': system_summary,
            'active_alerts': [
                {
                    'id': alert.alert_id,
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                    'acknowledged': alert.acknowledged
                }
                for alert in self.active_alerts.values()
            ],
            'performance_stats': self.performance_stats,
            'monitoring_status': {
                'is_running': self.is_running,
                'uptime': current_time - self.start_time if hasattr(self, 'start_time') else 0,
                'metrics_count': len(self.current_metrics),
                'alerts_count': len(self.active_alerts)
            }
        }
    
    def get_metrics_history(self, metric_name: str, duration: int = 3600) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric."""
        if metric_name not in self.metrics_history:
            return []
        
        current_time = time.time()
        cutoff_time = current_time - duration
        
        return [
            {
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp,
                'metadata': metric.metadata
            }
            for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False
    
    def set_alert_threshold(self, metric_name: str, threshold: float):
        """Set alert threshold for a metric."""
        self.alert_thresholds[metric_name] = threshold
        logger.info(f"Set alert threshold for {metric_name}: {threshold}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system monitor statistics."""
        return {
            'performance_stats': self.performance_stats.copy(),
            'metrics_count': len(self.current_metrics),
            'active_alerts': len(self.active_alerts),
            'alert_history_size': len(self.alert_history),
            'is_running': self.is_running
        }
    
    async def restart(self):
        """Restart the system monitor."""
        logger.info("Restarting System Monitor...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()
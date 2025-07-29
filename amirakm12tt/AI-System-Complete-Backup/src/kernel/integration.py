"""
Kernel-Level Integration Module
Provides deep system control, monitoring, and driver management
"""

import asyncio
import logging
import os
import platform
import subprocess
import ctypes
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import psutil
import signal

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class KernelManager:
    """Manages kernel-level integration and system monitoring."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        self.system_info = {}
        self.drivers = {}
        self.monitoring_tasks = {}
        self.system_hooks = {}
        
        # System detection
        self.platform = platform.system().lower()
        self.architecture = platform.machine()
        self.is_admin = self._check_admin_privileges()
        
        logger.info(f"Kernel Manager initialized for {self.platform} ({self.architecture})")
        
    def _check_admin_privileges(self) -> bool:
        """Check if running with administrator/root privileges."""
        try:
            if self.platform == 'windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception as e:
            logger.warning(f"Could not check admin privileges: {e}")
            return False
    
    async def initialize(self):
        """Initialize kernel integration."""
        logger.info("Initializing Kernel Manager...")
        
        try:
            # Gather system information
            await self._gather_system_info()
            
            # Initialize system monitoring
            await self._initialize_monitoring()
            
            # Load kernel drivers if available
            if self.is_admin:
                await self._load_drivers()
            else:
                logger.warning("Not running with admin privileges - limited kernel access")
            
            # Setup system hooks
            await self._setup_system_hooks()
            
            logger.info("Kernel Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kernel Manager: {e}")
            raise
    
    async def start(self):
        """Start kernel monitoring and services."""
        logger.info("Starting Kernel Manager...")
        
        try:
            # Start monitoring tasks
            self.monitoring_tasks['system_monitor'] = asyncio.create_task(
                self._system_monitoring_loop()
            )
            self.monitoring_tasks['resource_monitor'] = asyncio.create_task(
                self._resource_monitoring_loop()
            )
            self.monitoring_tasks['process_monitor'] = asyncio.create_task(
                self._process_monitoring_loop()
            )
            self.monitoring_tasks['security_monitor'] = asyncio.create_task(
                self._security_monitoring_loop()
            )
            
            self.is_running = True
            logger.info("Kernel Manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Kernel Manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown kernel manager gracefully."""
        logger.info("Shutting down Kernel Manager...")
        
        self.is_running = False
        
        # Cancel monitoring tasks
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Unload drivers
        await self._unload_drivers()
        
        # Remove system hooks
        await self._remove_system_hooks()
        
        logger.info("Kernel Manager shutdown complete")
    
    async def _gather_system_info(self):
        """Gather comprehensive system information."""
        self.system_info = {
            'platform': self.platform,
            'architecture': self.architecture,
            'kernel_version': platform.release(),
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': {},
            'network_interfaces': {},
            'boot_time': psutil.boot_time(),
            'admin_privileges': self.is_admin
        }
        
        # Get disk usage for all mounted drives
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.system_info['disk_usage'][partition.device] = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': (usage.used / usage.total) * 100
                }
            except Exception as e:
                logger.warning(f"Could not get disk usage for {partition.device}: {e}")
        
        # Get network interfaces
        for interface, addresses in psutil.net_if_addrs().items():
            self.system_info['network_interfaces'][interface] = []
            for addr in addresses:
                self.system_info['network_interfaces'][interface].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
    
    async def _initialize_monitoring(self):
        """Initialize system monitoring capabilities."""
        logger.info("Initializing system monitoring...")
        
        # Set up performance counters
        self.performance_counters = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'network_io': [],
            'process_count': [],
            'thread_count': []
        }
        
        # Initialize baseline measurements
        self.baseline_metrics = {
            'cpu_times': psutil.cpu_times(),
            'memory': psutil.virtual_memory(),
            'disk_io': psutil.disk_io_counters(),
            'network_io': psutil.net_io_counters()
        }
    
    async def _load_drivers(self):
        """Load kernel drivers if available."""
        driver_path = Path(self.config.kernel.driver_path)
        
        if not driver_path.exists():
            logger.info("No driver directory found, skipping driver loading")
            return
        
        logger.info(f"Loading drivers from {driver_path}")
        
        # Platform-specific driver loading
        if self.platform == 'windows':
            await self._load_windows_drivers(driver_path)
        elif self.platform == 'linux':
            await self._load_linux_drivers(driver_path)
        else:
            logger.warning(f"Driver loading not implemented for {self.platform}")
    
    async def _load_windows_drivers(self, driver_path: Path):
        """Load Windows kernel drivers."""
        for driver_file in driver_path.glob("*.sys"):
            try:
                # Use sc command to install and start driver
                driver_name = driver_file.stem
                
                # Install driver service
                install_cmd = [
                    'sc', 'create', driver_name,
                    'binPath=', str(driver_file.absolute()),
                    'type=', 'kernel'
                ]
                
                result = subprocess.run(install_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # Start driver service
                    start_cmd = ['sc', 'start', driver_name]
                    start_result = subprocess.run(start_cmd, capture_output=True, text=True)
                    
                    if start_result.returncode == 0:
                        self.drivers[driver_name] = {
                            'path': str(driver_file),
                            'status': 'loaded',
                            'type': 'kernel'
                        }
                        logger.info(f"Loaded Windows driver: {driver_name}")
                    else:
                        logger.error(f"Failed to start driver {driver_name}: {start_result.stderr}")
                else:
                    logger.error(f"Failed to install driver {driver_name}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error loading Windows driver {driver_file}: {e}")
    
    async def _load_linux_drivers(self, driver_path: Path):
        """Load Linux kernel modules."""
        for module_file in driver_path.glob("*.ko"):
            try:
                # Use insmod to load kernel module
                cmd = ['insmod', str(module_file.absolute())]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    module_name = module_file.stem
                    self.drivers[module_name] = {
                        'path': str(module_file),
                        'status': 'loaded',
                        'type': 'module'
                    }
                    logger.info(f"Loaded Linux kernel module: {module_name}")
                else:
                    logger.error(f"Failed to load module {module_file}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error loading Linux module {module_file}: {e}")
    
    async def _unload_drivers(self):
        """Unload all loaded drivers."""
        for driver_name, driver_info in self.drivers.items():
            try:
                if self.platform == 'windows':
                    # Stop and delete Windows service
                    subprocess.run(['sc', 'stop', driver_name], capture_output=True)
                    subprocess.run(['sc', 'delete', driver_name], capture_output=True)
                elif self.platform == 'linux':
                    # Remove Linux kernel module
                    subprocess.run(['rmmod', driver_name], capture_output=True)
                
                logger.info(f"Unloaded driver: {driver_name}")
                
            except Exception as e:
                logger.error(f"Error unloading driver {driver_name}: {e}")
    
    async def _setup_system_hooks(self):
        """Setup system-level hooks for monitoring."""
        try:
            # Setup signal handlers for system events
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, self._handle_system_signal)
            if hasattr(signal, 'SIGUSR2'):
                signal.signal(signal.SIGUSR2, self._handle_system_signal)
            
            logger.info("System hooks setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up system hooks: {e}")
    
    async def _remove_system_hooks(self):
        """Remove system hooks."""
        try:
            # Reset signal handlers
            if hasattr(signal, 'SIGUSR1'):
                signal.signal(signal.SIGUSR1, signal.SIG_DFL)
            if hasattr(signal, 'SIGUSR2'):
                signal.signal(signal.SIGUSR2, signal.SIG_DFL)
            
            logger.info("System hooks removed")
            
        except Exception as e:
            logger.error(f"Error removing system hooks: {e}")
    
    def _handle_system_signal(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received system signal: {signum}")
        # Handle system events based on signal
    
    async def _system_monitoring_loop(self):
        """Main system monitoring loop."""
        while self.is_running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                
                # Update performance counters
                self.performance_counters['cpu_usage'].append(cpu_percent)
                self.performance_counters['memory_usage'].append(memory.percent)
                
                # Keep only recent samples
                max_samples = 1000
                for counter in self.performance_counters.values():
                    if len(counter) > max_samples:
                        counter[:] = counter[-max_samples:]
                
                # Check for alerts
                await self._check_performance_alerts(cpu_percent, memory.percent)
                
                await asyncio.sleep(self.config.kernel.monitoring_interval / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(1)
    
    async def _resource_monitoring_loop(self):
        """Monitor system resources."""
        while self.is_running:
            try:
                # Monitor disk usage
                for device, usage_info in self.system_info['disk_usage'].items():
                    try:
                        current_usage = psutil.disk_usage(device)
                        usage_percent = (current_usage.used / current_usage.total) * 100
                        
                        if usage_percent > 90:
                            logger.warning(f"High disk usage on {device}: {usage_percent:.1f}%")
                    except Exception:
                        pass
                
                # Monitor memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 85:
                    logger.warning(f"High memory usage: {memory.percent:.1f}%")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_monitoring_loop(self):
        """Monitor system processes."""
        while self.is_running:
            try:
                # Get process information
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Update process count
                self.performance_counters['process_count'].append(len(processes))
                
                # Find high resource usage processes
                high_cpu_processes = [p for p in processes if p['cpu_percent'] > 80]
                high_memory_processes = [p for p in processes if p['memory_percent'] > 20]
                
                if high_cpu_processes:
                    logger.info(f"High CPU processes: {high_cpu_processes}")
                if high_memory_processes:
                    logger.info(f"High memory processes: {high_memory_processes}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process monitoring loop: {e}")
                await asyncio.sleep(1)
    
    async def _security_monitoring_loop(self):
        """Monitor for security events."""
        while self.is_running:
            try:
                # Monitor for suspicious processes
                suspicious_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        # Check for suspicious process names or command lines
                        if self._is_suspicious_process(proc.info):
                            suspicious_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                if suspicious_processes:
                    logger.warning(f"Suspicious processes detected: {suspicious_processes}")
                
                # Monitor network connections
                connections = psutil.net_connections()
                suspicious_connections = [
                    conn for conn in connections
                    if self._is_suspicious_connection(conn)
                ]
                
                if suspicious_connections:
                    logger.warning(f"Suspicious network connections: {suspicious_connections}")
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in security monitoring loop: {e}")
                await asyncio.sleep(1)
    
    def _is_suspicious_process(self, proc_info: Dict[str, Any]) -> bool:
        """Check if a process is suspicious."""
        suspicious_names = ['keylogger', 'backdoor', 'trojan', 'malware']
        process_name = proc_info.get('name', '').lower()
        
        return any(suspicious in process_name for suspicious in suspicious_names)
    
    def _is_suspicious_connection(self, connection) -> bool:
        """Check if a network connection is suspicious."""
        # Check for connections to known malicious IPs or ports
        # This is a simplified check - in practice, you'd use threat intelligence
        suspicious_ports = [1337, 31337, 4444, 5555]
        
        if hasattr(connection, 'laddr') and connection.laddr:
            return connection.laddr.port in suspicious_ports
        
        return False
    
    async def _check_performance_alerts(self, cpu_percent: float, memory_percent: float):
        """Check for performance alerts."""
        thresholds = self.config.monitoring.alert_thresholds
        
        if cpu_percent > thresholds.get('cpu_usage', 80):
            logger.warning(f"High CPU usage alert: {cpu_percent:.1f}%")
        
        if memory_percent > thresholds.get('memory_usage', 85):
            logger.warning(f"High memory usage alert: {memory_percent:.1f}%")
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Check if monitoring tasks are running
            active_tasks = sum(1 for task in self.monitoring_tasks.values() if not task.done())
            
            if active_tasks == len(self.monitoring_tasks):
                return "healthy"
            elif active_tasks > 0:
                return "degraded"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        return self.system_info.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': {
                    device: (usage['used'] / usage['total']) * 100
                    for device, usage in self.system_info['disk_usage'].items()
                },
                'process_count': len(psutil.pids()),
                'uptime': psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def get_driver_status(self) -> Dict[str, Any]:
        """Get status of loaded drivers."""
        return self.drivers.copy()
    
    async def execute_system_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute a system command safely."""
        if not self.is_admin:
            return {'success': False, 'error': 'Admin privileges required'}
        
        try:
            cmd = [command] + (args or [])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def restart(self):
        """Restart the kernel manager."""
        logger.info("Restarting Kernel Manager...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()
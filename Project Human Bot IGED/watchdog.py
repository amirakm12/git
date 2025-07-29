"""
Watchdog for IGED
System monitoring and health checks
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Try to import psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class Watchdog:
    def __init__(self, components):
        self.components = components
        self.running = False
        self.monitoring_thread = None
        self.health_checks = []
        self.system_stats = {}
        
        # Initialize health checks
        self.setup_health_checks()
    
    def setup_health_checks(self):
        """Setup system health checks"""
        self.health_checks = [
            self._check_system_resources,
            self._check_component_health,
            self._check_memory_usage,
            self._check_disk_space
        ]
    
    def run(self):
        """Start the watchdog monitoring"""
        if self.running:
            logger.warning("Watchdog already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("🔄 Watchdog monitoring started")
    
    def stop(self):
        """Stop the watchdog monitoring"""
        self.running = False
        logger.info("🛑 Watchdog monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Run health checks
                for check in self.health_checks:
                    try:
                        check()
                    except Exception as e:
                        logger.error(f"Health check failed: {e}")
                
                # Update system stats
                self._update_system_stats()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Watchdog monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_system_resources(self):
        """Check system resource usage"""
        try:
            if not PSUTIL_AVAILABLE:
                logger.warning("⚠️ psutil not available, skipping system resource check")
                return
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Log warnings for high usage
            if cpu_percent > 80:
                logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                logger.warning(f"⚠️ High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                logger.warning(f"⚠️ Low disk space: {100 - disk.percent}% free")
            
            # Store stats
            self.system_stats['cpu_percent'] = cpu_percent
            self.system_stats['memory_percent'] = memory.percent
            self.system_stats['disk_percent'] = disk.percent
            self.system_stats['last_check'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
    
    def _check_component_health(self):
        """Check component health"""
        try:
            component_status = {}
            
            # Check voice pipeline
            if 'voice' in self.components:
                voice = self.components['voice']
                component_status['voice'] = {
                    'listening': voice.is_listening,
                    'whisper_loaded': voice.whisper_model is not None
                }
            
            # Check orchestrator
            if 'orchestrator' in self.components:
                orch = self.components['orchestrator']
                component_status['orchestrator'] = {
                    'agents_count': len(orch.agents),
                    'plugins_count': len(orch.plugins)
                }
            
            # Check memory engine
            if 'memory' in self.components:
                memory = self.components['memory']
                stats = memory.get_statistics()
                component_status['memory'] = {
                    'total_entries': stats.get('total_entries', 0),
                    'success_rate': stats.get('success_rate', 0)
                }
            
            # Log component status
            for component, status in component_status.items():
                logger.debug(f"Component {component}: {status}")
            
            self.system_stats['components'] = component_status
            
        except Exception as e:
            logger.error(f"Component health check failed: {e}")
    
    def _check_memory_usage(self):
        """Check memory engine usage"""
        try:
            if 'memory' in self.components:
                memory = self.components['memory']
                stats = memory.get_statistics()
                
                # Check for memory growth
                total_entries = stats.get('total_entries', 0)
                if total_entries > 10000:
                    logger.warning(f"⚠️ Large memory database: {total_entries} entries")
                
                # Check success rate
                success_rate = stats.get('success_rate', 100)
                if success_rate < 80:
                    logger.warning(f"⚠️ Low success rate: {success_rate}%")
                
        except Exception as e:
            logger.error(f"Memory usage check failed: {e}")
    
    def _check_disk_space(self):
        """Check disk space for output files"""
        try:
            output_dirs = ['output', 'memory', 'logs']
            
            for dir_name in output_dirs:
                try:
                    import os
                    if os.path.exists(dir_name):
                        total_size = 0
                        file_count = 0
                        
                        for root, dirs, files in os.walk(dir_name):
                            for file in files:
                                file_path = os.path.join(root, file)
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                        
                        # Log if directory is getting large
                        if total_size > 100 * 1024 * 1024:  # 100MB
                            logger.warning(f"⚠️ Large output directory {dir_name}: {total_size / 1024 / 1024:.1f}MB")
                        
                        self.system_stats[f'{dir_name}_size'] = total_size
                        self.system_stats[f'{dir_name}_files'] = file_count
                        
                except Exception as e:
                    logger.error(f"Failed to check directory {dir_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
    
    def _update_system_stats(self):
        """Update system statistics"""
        try:
            if not PSUTIL_AVAILABLE:
                logger.warning("⚠️ psutil not available, skipping process stats")
                return
            
            # Get process info
            process = psutil.Process()
            self.system_stats['process'] = {
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
            
            # Get network info
            net_io = psutil.net_io_counters()
            self.system_stats['network'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
        except Exception as e:
            logger.error(f"Failed to update system stats: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'watchdog_running': self.running,
                'system_stats': self.system_stats.copy(),
                'health_status': 'healthy'
            }
            
            # Determine overall health
            issues = []
            
            # Check CPU usage
            cpu_percent = self.system_stats.get('cpu_percent', 0)
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            # Check memory usage
            memory_percent = self.system_stats.get('memory_percent', 0)
            if memory_percent > 80:
                issues.append(f"High memory usage: {memory_percent}%")
            
            # Check disk usage
            disk_percent = self.system_stats.get('disk_percent', 0)
            if disk_percent > 90:
                issues.append(f"Low disk space: {100 - disk_percent}% free")
            
            # Check component health
            components = self.system_stats.get('components', {})
            for component, status in components.items():
                if component == 'voice' and not status.get('whisper_loaded', False):
                    issues.append("Whisper model not loaded")
                elif component == 'memory' and status.get('success_rate', 100) < 80:
                    issues.append(f"Low memory success rate: {status.get('success_rate', 100)}%")
            
            if issues:
                report['health_status'] = 'warning'
                report['issues'] = issues
            else:
                report['health_status'] = 'healthy'
                report['issues'] = []
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'health_status': 'error',
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get watchdog status"""
        return {
            'running': self.running,
            'last_check': self.system_stats.get('last_check', 'never'),
            'health_status': self.get_health_report()['health_status']
        } 
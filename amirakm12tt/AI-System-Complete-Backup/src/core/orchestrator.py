"""
System Orchestrator
Central coordination and management of all system components
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json

from .config import SystemConfig

logger = logging.getLogger(__name__)

class SystemState(Enum):
    """System state enumeration."""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class ComponentStatus:
    """Status information for a system component."""
    name: str
    state: str
    health: str
    last_heartbeat: float
    error_count: int
    performance_metrics: Dict[str, Any]
    
@dataclass
class SystemMetrics:
    """System-wide metrics."""
    uptime: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    active_components: int
    memory_usage: float
    cpu_usage: float

class SystemOrchestrator:
    """Central orchestrator for the AI system."""
    
    def __init__(self, config: SystemConfig, components: Dict[str, Any]):
        self.config = config
        self.components = components
        self.state = SystemState.INITIALIZING
        self.is_running = False
        
        # Component management
        self.component_status = {}
        self.component_tasks = {}
        self.heartbeat_interval = 10  # seconds
        
        # System metrics
        self.start_time = time.time()
        self.metrics = SystemMetrics(
            uptime=0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            average_response_time=0,
            active_components=0,
            memory_usage=0,
            cpu_usage=0
        )
        
        # Task queues and coordination
        self.task_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.event_bus = asyncio.Queue()
        
        # Performance tracking
        self.response_times = []
        self.max_response_time_samples = 1000
        
        logger.info("System Orchestrator initialized")
    
    async def initialize(self):
        """Initialize the orchestrator."""
        logger.info("Initializing System Orchestrator...")
        
        # Initialize component status tracking
        for component_name in self.components:
            self.component_status[component_name] = ComponentStatus(
                name=component_name,
                state="initialized",
                health="unknown",
                last_heartbeat=time.time(),
                error_count=0,
                performance_metrics={}
            )
        
        self.state = SystemState.STARTING
        logger.info("System Orchestrator initialization complete")
    
    async def start(self):
        """Start the orchestrator and begin coordination."""
        logger.info("Starting System Orchestrator...")
        
        try:
            # Start background tasks
            self.component_tasks['heartbeat_monitor'] = asyncio.create_task(
                self._heartbeat_monitor()
            )
            self.component_tasks['task_processor'] = asyncio.create_task(
                self._task_processor()
            )
            self.component_tasks['event_processor'] = asyncio.create_task(
                self._event_processor()
            )
            self.component_tasks['metrics_collector'] = asyncio.create_task(
                self._metrics_collector()
            )
            self.component_tasks['health_checker'] = asyncio.create_task(
                self._health_checker()
            )
            
            self.is_running = True
            self.state = SystemState.RUNNING
            
            logger.info("System Orchestrator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start System Orchestrator: {e}")
            self.state = SystemState.ERROR
            raise
    
    async def shutdown(self):
        """Shutdown the orchestrator gracefully."""
        logger.info("Shutting down System Orchestrator...")
        
        self.is_running = False
        self.state = SystemState.STOPPING
        
        # Cancel all background tasks
        for task_name, task in self.component_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled task: {task_name}")
        
        self.component_tasks.clear()
        self.state = SystemState.STOPPED
        
        logger.info("System Orchestrator shutdown complete")
    
    async def _heartbeat_monitor(self):
        """Monitor component heartbeats."""
        while self.is_running:
            try:
                current_time = time.time()
                
                for component_name, status in self.component_status.items():
                    # Check if component is responsive
                    time_since_heartbeat = current_time - status.last_heartbeat
                    
                    if time_since_heartbeat > self.heartbeat_interval * 2:
                        if status.health != "unresponsive":
                            logger.warning(f"Component {component_name} is unresponsive")
                            status.health = "unresponsive"
                            await self._handle_component_failure(component_name)
                    elif status.health == "unresponsive":
                        logger.info(f"Component {component_name} is responsive again")
                        status.health = "healthy"
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(1)
    
    async def _task_processor(self):
        """Process tasks from the task queue."""
        while self.is_running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                start_time = time.time()
                
                # Process the task
                result = await self._execute_task(task)
                
                # Calculate response time
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                
                # Put result in result queue
                await self.result_queue.put({
                    'task_id': task.get('id'),
                    'result': result,
                    'response_time': response_time,
                    'timestamp': time.time()
                })
                
                self.metrics.total_requests += 1
                if result.get('success', False):
                    self.metrics.successful_requests += 1
                else:
                    self.metrics.failed_requests += 1
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(1)
    
    async def _event_processor(self):
        """Process events from the event bus."""
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.event_bus.get(),
                    timeout=1.0
                )
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                await asyncio.sleep(1)
    
    async def _metrics_collector(self):
        """Collect system metrics periodically."""
        while self.is_running:
            try:
                await self._update_system_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(1)
    
    async def _health_checker(self):
        """Perform periodic health checks on components."""
        while self.is_running:
            try:
                for component_name, component in self.components.items():
                    if hasattr(component, 'health_check'):
                        try:
                            health_status = await component.health_check()
                            self.component_status[component_name].health = health_status
                            self.component_status[component_name].last_heartbeat = time.time()
                        except Exception as e:
                            logger.error(f"Health check failed for {component_name}: {e}")
                            self.component_status[component_name].health = "unhealthy"
                            self.component_status[component_name].error_count += 1
                
                await asyncio.sleep(60)  # Health check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health checker: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using appropriate components."""
        task_type = task.get('type')
        target_component = task.get('component')
        
        try:
            if target_component and target_component in self.components:
                component = self.components[target_component]
                if hasattr(component, 'execute_task'):
                    result = await component.execute_task(task)
                    return {'success': True, 'result': result}
                else:
                    return {'success': False, 'error': f"Component {target_component} does not support task execution"}
            else:
                # Route task based on type
                result = await self._route_task(task)
                return {'success': True, 'result': result}
                
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _route_task(self, task: Dict[str, Any]) -> Any:
        """Route task to appropriate component based on task type."""
        task_type = task.get('type')
        
        if task_type == 'triage':
            return await self.components['triage_agent'].process_request(task['data'])
        elif task_type == 'research':
            return await self.components['research_agent'].conduct_research(task['data'])
        elif task_type == 'orchestration':
            return await self.components['orchestration_agent'].orchestrate(task['data'])
        elif task_type == 'rag_query':
            return await self.components['rag_engine'].query(task['data'])
        elif task_type == 'speculative_decode':
            return await self.components['speculative_decoder'].decode(task['data'])
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle system events."""
        event_type = event.get('type')
        
        if event_type == 'component_error':
            await self._handle_component_error(event)
        elif event_type == 'performance_alert':
            await self._handle_performance_alert(event)
        elif event_type == 'security_alert':
            await self._handle_security_alert(event)
        elif event_type == 'system_command':
            await self._handle_system_command(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    async def _handle_component_failure(self, component_name: str):
        """Handle component failure."""
        logger.error(f"Handling failure for component: {component_name}")
        
        # Attempt to restart component if possible
        if component_name in self.components:
            component = self.components[component_name]
            if hasattr(component, 'restart'):
                try:
                    await component.restart()
                    logger.info(f"Successfully restarted component: {component_name}")
                    self.component_status[component_name].health = "healthy"
                    self.component_status[component_name].error_count = 0
                except Exception as e:
                    logger.error(f"Failed to restart component {component_name}: {e}")
    
    async def _handle_component_error(self, event: Dict[str, Any]):
        """Handle component error event."""
        component_name = event.get('component')
        error_details = event.get('error')
        
        logger.error(f"Component error in {component_name}: {error_details}")
        
        if component_name in self.component_status:
            self.component_status[component_name].error_count += 1
            
            # If too many errors, mark as unhealthy
            if self.component_status[component_name].error_count > 5:
                self.component_status[component_name].health = "unhealthy"
                await self._handle_component_failure(component_name)
    
    async def _handle_performance_alert(self, event: Dict[str, Any]):
        """Handle performance alert."""
        metric = event.get('metric')
        value = event.get('value')
        threshold = event.get('threshold')
        
        logger.warning(f"Performance alert: {metric} = {value} (threshold: {threshold})")
        
        # Take corrective action based on metric
        if metric == 'response_time' and value > threshold:
            await self._optimize_performance()
        elif metric == 'memory_usage' and value > threshold:
            await self._manage_memory()
    
    async def _handle_security_alert(self, event: Dict[str, Any]):
        """Handle security alert."""
        alert_type = event.get('alert_type')
        details = event.get('details')
        
        logger.critical(f"Security alert: {alert_type} - {details}")
        
        # Notify security monitor
        if 'security_monitor' in self.components:
            await self.components['security_monitor'].handle_alert(event)
    
    async def _handle_system_command(self, event: Dict[str, Any]):
        """Handle system command."""
        command = event.get('command')
        
        if command == 'pause':
            await self.pause_system()
        elif command == 'resume':
            await self.resume_system()
        elif command == 'restart':
            await self.restart_system()
        elif command == 'shutdown':
            await self.shutdown()
        else:
            logger.warning(f"Unknown system command: {command}")
    
    async def _update_system_metrics(self):
        """Update system-wide metrics."""
        current_time = time.time()
        self.metrics.uptime = current_time - self.start_time
        
        # Count active components
        active_count = sum(
            1 for status in self.component_status.values()
            if status.health in ['healthy', 'unknown']
        )
        self.metrics.active_components = active_count
        
        # Calculate average response time
        if self.response_times:
            self.metrics.average_response_time = sum(self.response_times) / len(self.response_times)
        
        # Get system resource usage (placeholder - would use actual system monitoring)
        self.metrics.memory_usage = 0.0  # Would get from system monitor
        self.metrics.cpu_usage = 0.0     # Would get from system monitor
    
    def _update_response_time(self, response_time: float):
        """Update response time tracking."""
        self.response_times.append(response_time)
        
        # Keep only recent samples
        if len(self.response_times) > self.max_response_time_samples:
            self.response_times = self.response_times[-self.max_response_time_samples:]
    
    async def _optimize_performance(self):
        """Optimize system performance."""
        logger.info("Optimizing system performance...")
        
        # Implement performance optimization strategies
        # This could include load balancing, resource allocation, etc.
    
    async def _manage_memory(self):
        """Manage memory usage."""
        logger.info("Managing memory usage...")
        
        # Implement memory management strategies
        # This could include garbage collection, cache clearing, etc.
    
    async def pause_system(self):
        """Pause system operation."""
        logger.info("Pausing system...")
        self.state = SystemState.PAUSING
        
        # Pause all components
        for component in self.components.values():
            if hasattr(component, 'pause'):
                await component.pause()
        
        self.state = SystemState.PAUSED
    
    async def resume_system(self):
        """Resume system operation."""
        logger.info("Resuming system...")
        
        # Resume all components
        for component in self.components.values():
            if hasattr(component, 'resume'):
                await component.resume()
        
        self.state = SystemState.RUNNING
    
    async def restart_system(self):
        """Restart the entire system."""
        logger.info("Restarting system...")
        
        await self.shutdown()
        await asyncio.sleep(2)  # Brief pause
        await self.start()
    
    # Public API methods
    
    async def submit_task(self, task: Dict[str, Any]) -> str:
        """Submit a task for processing."""
        task_id = f"task_{int(time.time() * 1000000)}"
        task['id'] = task_id
        
        await self.task_queue.put(task)
        return task_id
    
    async def get_result(self, task_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Get result for a task."""
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                result = await asyncio.wait_for(
                    self.result_queue.get(),
                    timeout=1.0
                )
                
                if result.get('task_id') == task_id:
                    return result
                else:
                    # Put back if not the right task
                    await self.result_queue.put(result)
                    
            except asyncio.TimeoutError:
                continue
        
        return None
    
    async def publish_event(self, event: Dict[str, Any]):
        """Publish an event to the event bus."""
        await self.event_bus.put(event)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'state': self.state.value,
            'uptime': time.time() - self.start_time,
            'components': {
                name: {
                    'state': status.state,
                    'health': status.health,
                    'error_count': status.error_count,
                    'last_heartbeat': status.last_heartbeat
                }
                for name, status in self.component_status.items()
            },
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'average_response_time': self.metrics.average_response_time,
                'active_components': self.metrics.active_components
            }
        }
    
    def get_component_status(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific component."""
        if component_name in self.component_status:
            status = self.component_status[component_name]
            return {
                'name': status.name,
                'state': status.state,
                'health': status.health,
                'last_heartbeat': status.last_heartbeat,
                'error_count': status.error_count,
                'performance_metrics': status.performance_metrics
            }
        return None
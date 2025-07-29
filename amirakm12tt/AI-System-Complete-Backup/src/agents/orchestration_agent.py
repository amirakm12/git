"""
Orchestration Agent
Coordinates multi-agent workflows and system orchestration
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from collections import defaultdict, deque
import uuid

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class AgentRole(Enum):
    """Available agent roles."""
    TRIAGE = "triage"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    MONITORING = "monitoring"
    SYSTEM_CONTROL = "system_control"

@dataclass
class WorkflowTask:
    """Individual task within a workflow."""
    task_id: str
    agent_role: AgentRole
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    priority: TaskPriority
    timeout: float
    retry_count: int
    metadata: Dict[str, Any]

@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    global_timeout: float
    max_retries: int
    failure_strategy: str  # "abort", "continue", "retry"
    metadata: Dict[str, Any]

@dataclass
class WorkflowExecution:
    """Workflow execution state."""
    workflow_id: str
    execution_id: str
    definition: WorkflowDefinition
    status: WorkflowStatus
    start_time: float
    end_time: Optional[float]
    task_results: Dict[str, Any]
    current_tasks: List[str]
    completed_tasks: List[str]
    failed_tasks: List[str]
    progress: float
    metadata: Dict[str, Any]

class OrchestrationAgent:
    """Agent responsible for orchestrating multi-agent workflows."""
    
    def __init__(self, config: SystemConfig, triage_agent, research_agent):
        self.config = config
        self.triage_agent = triage_agent
        self.research_agent = research_agent
        self.is_running = False
        
        # Workflow management
        self.workflow_definitions = {}
        self.active_executions = {}
        self.execution_history = deque(maxlen=1000)
        self.execution_queue = asyncio.Queue()
        
        # Agent registry
        self.agent_registry = {
            AgentRole.TRIAGE: triage_agent,
            AgentRole.RESEARCH: research_agent,
            # Additional agents will be registered dynamically
        }
        
        # Built-in workflow templates
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Performance metrics
        self.metrics = {
            'total_workflows': 0,
            'completed_workflows': 0,
            'failed_workflows': 0,
            'average_execution_time': 0.0,
            'success_rate': 0.0,
            'workflows_by_type': defaultdict(int),
            'agent_utilization': defaultdict(float)
        }
        
        # Execution engine
        self.execution_semaphore = asyncio.Semaphore(self.config.agents.max_concurrent_tasks)
        
        logger.info("Orchestration Agent initialized")
    
    def _initialize_workflow_templates(self) -> Dict[str, WorkflowDefinition]:
        """Initialize built-in workflow templates."""
        templates = {}
        
        # Information Gathering Workflow
        templates['information_gathering'] = WorkflowDefinition(
            workflow_id='info_gather_template',
            name='Information Gathering',
            description='Comprehensive information gathering and analysis',
            tasks=[
                WorkflowTask(
                    task_id='triage_request',
                    agent_role=AgentRole.TRIAGE,
                    action='process_request',
                    parameters={'request': '{query}'},
                    dependencies=[],
                    priority=TaskPriority.HIGH,
                    timeout=30.0,
                    retry_count=2,
                    metadata={'stage': 'initial_triage'}
                ),
                WorkflowTask(
                    task_id='conduct_research',
                    agent_role=AgentRole.RESEARCH,
                    action='conduct_research',
                    parameters={
                        'query': '{query}',
                        'research_type': 'literature_review',
                        'depth_level': 3
                    },
                    dependencies=['triage_request'],
                    priority=TaskPriority.NORMAL,
                    timeout=300.0,
                    retry_count=1,
                    metadata={'stage': 'research'}
                ),
                WorkflowTask(
                    task_id='synthesize_results',
                    agent_role=AgentRole.ANALYSIS,
                    action='synthesize',
                    parameters={
                        'triage_result': '{triage_request.result}',
                        'research_result': '{conduct_research.result}'
                    },
                    dependencies=['triage_request', 'conduct_research'],
                    priority=TaskPriority.NORMAL,
                    timeout=60.0,
                    retry_count=1,
                    metadata={'stage': 'synthesis'}
                )
            ],
            global_timeout=600.0,
            max_retries=2,
            failure_strategy='retry',
            metadata={'category': 'information', 'complexity': 'medium'}
        )
        
        # System Analysis Workflow
        templates['system_analysis'] = WorkflowDefinition(
            workflow_id='system_analysis_template',
            name='System Analysis',
            description='Comprehensive system analysis and monitoring',
            tasks=[
                WorkflowTask(
                    task_id='gather_system_info',
                    agent_role=AgentRole.MONITORING,
                    action='get_system_status',
                    parameters={},
                    dependencies=[],
                    priority=TaskPriority.HIGH,
                    timeout=30.0,
                    retry_count=2,
                    metadata={'stage': 'data_collection'}
                ),
                WorkflowTask(
                    task_id='analyze_performance',
                    agent_role=AgentRole.ANALYSIS,
                    action='analyze_performance',
                    parameters={'system_data': '{gather_system_info.result}'},
                    dependencies=['gather_system_info'],
                    priority=TaskPriority.NORMAL,
                    timeout=120.0,
                    retry_count=1,
                    metadata={'stage': 'analysis'}
                ),
                WorkflowTask(
                    task_id='generate_recommendations',
                    agent_role=AgentRole.RESEARCH,
                    action='conduct_research',
                    parameters={
                        'query': 'system optimization recommendations',
                        'research_type': 'problem_solving',
                        'depth_level': 2
                    },
                    dependencies=['analyze_performance'],
                    priority=TaskPriority.NORMAL,
                    timeout=180.0,
                    retry_count=1,
                    metadata={'stage': 'recommendations'}
                )
            ],
            global_timeout=450.0,
            max_retries=1,
            failure_strategy='continue',
            metadata={'category': 'system', 'complexity': 'high'}
        )
        
        # Problem Resolution Workflow
        templates['problem_resolution'] = WorkflowDefinition(
            workflow_id='problem_resolution_template',
            name='Problem Resolution',
            description='Systematic problem analysis and resolution',
            tasks=[
                WorkflowTask(
                    task_id='problem_triage',
                    agent_role=AgentRole.TRIAGE,
                    action='process_request',
                    parameters={'request': '{problem_description}'},
                    dependencies=[],
                    priority=TaskPriority.URGENT,
                    timeout=20.0,
                    retry_count=3,
                    metadata={'stage': 'problem_identification'}
                ),
                WorkflowTask(
                    task_id='root_cause_analysis',
                    agent_role=AgentRole.RESEARCH,
                    action='conduct_research',
                    parameters={
                        'query': '{problem_description}',
                        'research_type': 'problem_solving',
                        'depth_level': 4
                    },
                    dependencies=['problem_triage'],
                    priority=TaskPriority.HIGH,
                    timeout=240.0,
                    retry_count=2,
                    metadata={'stage': 'root_cause_analysis'}
                ),
                WorkflowTask(
                    task_id='solution_implementation',
                    agent_role=AgentRole.SYSTEM_CONTROL,
                    action='implement_solution',
                    parameters={
                        'solution': '{root_cause_analysis.result.recommended_solution}',
                        'safety_checks': True
                    },
                    dependencies=['root_cause_analysis'],
                    priority=TaskPriority.HIGH,
                    timeout=300.0,
                    retry_count=1,
                    metadata={'stage': 'implementation'}
                ),
                WorkflowTask(
                    task_id='verify_resolution',
                    agent_role=AgentRole.MONITORING,
                    action='verify_fix',
                    parameters={
                        'original_problem': '{problem_description}',
                        'applied_solution': '{solution_implementation.result}'
                    },
                    dependencies=['solution_implementation'],
                    priority=TaskPriority.NORMAL,
                    timeout=60.0,
                    retry_count=2,
                    metadata={'stage': 'verification'}
                )
            ],
            global_timeout=900.0,
            max_retries=2,
            failure_strategy='abort',
            metadata={'category': 'problem_resolution', 'complexity': 'high'}
        )
        
        return templates
    
    async def initialize(self):
        """Initialize the orchestration agent."""
        logger.info("Initializing Orchestration Agent...")
        
        try:
            # Load workflow definitions
            await self._load_workflow_definitions()
            
            # Initialize execution engine
            await self._initialize_execution_engine()
            
            logger.info("Orchestration Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Orchestration Agent: {e}")
            raise
    
    async def start(self):
        """Start the orchestration agent."""
        logger.info("Starting Orchestration Agent...")
        
        try:
            # Start background tasks
            self.background_tasks = {
                'workflow_executor': asyncio.create_task(self._workflow_execution_loop()),
                'metrics_collector': asyncio.create_task(self._metrics_collection_loop()),
                'cleanup_manager': asyncio.create_task(self._cleanup_management_loop()),
                'health_monitor': asyncio.create_task(self._health_monitoring_loop())
            }
            
            self.is_running = True
            logger.info("Orchestration Agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Orchestration Agent: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the orchestration agent."""
        logger.info("Shutting down Orchestration Agent...")
        
        self.is_running = False
        
        # Cancel all active executions
        for execution_id, execution in self.active_executions.items():
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.CANCELLED
                logger.info(f"Cancelled workflow execution {execution_id}")
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Save execution history
        await self._save_execution_history()
        
        logger.info("Orchestration Agent shutdown complete")
    
    async def orchestrate(self, workflow_name: str, parameters: Dict[str, Any] = None,
                         custom_workflow: WorkflowDefinition = None) -> WorkflowExecution:
        """Orchestrate a workflow execution."""
        
        # Use custom workflow or get from templates
        if custom_workflow:
            workflow_def = custom_workflow
        elif workflow_name in self.workflow_templates:
            workflow_def = self.workflow_templates[workflow_name]
        elif workflow_name in self.workflow_definitions:
            workflow_def = self.workflow_definitions[workflow_name]
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        # Create execution
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            workflow_id=workflow_def.workflow_id,
            execution_id=execution_id,
            definition=workflow_def,
            status=WorkflowStatus.PENDING,
            start_time=time.time(),
            end_time=None,
            task_results={},
            current_tasks=[],
            completed_tasks=[],
            failed_tasks=[],
            progress=0.0,
            metadata={
                'parameters': parameters or {},
                'created_at': time.time()
            }
        )
        
        # Add to active executions
        self.active_executions[execution_id] = execution
        
        # Queue for execution
        await self.execution_queue.put(execution_id)
        
        logger.info(f"Queued workflow execution {execution_id} for workflow {workflow_name}")
        
        return execution
    
    async def _workflow_execution_loop(self):
        """Main workflow execution loop."""
        while self.is_running:
            try:
                # Get next execution from queue
                execution_id = await asyncio.wait_for(
                    self.execution_queue.get(),
                    timeout=1.0
                )
                
                if execution_id in self.active_executions:
                    execution = self.active_executions[execution_id]
                    
                    # Execute workflow
                    async with self.execution_semaphore:
                        await self._execute_workflow(execution)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in workflow execution loop: {e}")
                await asyncio.sleep(1)
    
    async def _execute_workflow(self, execution: WorkflowExecution):
        """Execute a single workflow."""
        logger.info(f"Starting execution of workflow {execution.execution_id}")
        
        try:
            execution.status = WorkflowStatus.RUNNING
            start_time = time.time()
            
            # Build dependency graph
            task_graph = self._build_task_graph(execution.definition.tasks)
            
            # Execute tasks based on dependencies
            await self._execute_task_graph(execution, task_graph)
            
            # Check final status
            if len(execution.failed_tasks) == 0:
                execution.status = WorkflowStatus.COMPLETED
                self.metrics['completed_workflows'] += 1
            else:
                execution.status = WorkflowStatus.FAILED
                self.metrics['failed_workflows'] += 1
            
            execution.end_time = time.time()
            execution.progress = 1.0
            
            # Update metrics
            self.metrics['total_workflows'] += 1
            execution_time = execution.end_time - start_time
            
            # Update average execution time
            total_completed = self.metrics['completed_workflows'] + self.metrics['failed_workflows']
            if total_completed > 1:
                self.metrics['average_execution_time'] = (
                    (self.metrics['average_execution_time'] * (total_completed - 1) + execution_time) / total_completed
                )
            else:
                self.metrics['average_execution_time'] = execution_time
            
            # Update success rate
            self.metrics['success_rate'] = self.metrics['completed_workflows'] / self.metrics['total_workflows']
            
            # Move to history
            self.execution_history.append(execution)
            
            logger.info(f"Completed workflow execution {execution.execution_id} with status {execution.status.value}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {execution.execution_id}: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.end_time = time.time()
            execution.metadata['error'] = str(e)
            self.execution_history.append(execution)
        
        finally:
            # Remove from active executions
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
    
    def _build_task_graph(self, tasks: List[WorkflowTask]) -> Dict[str, Dict[str, Any]]:
        """Build task dependency graph."""
        graph = {}
        
        for task in tasks:
            graph[task.task_id] = {
                'task': task,
                'dependencies': set(task.dependencies),
                'dependents': set(),
                'status': 'pending'
            }
        
        # Build reverse dependencies (dependents)
        for task_id, task_info in graph.items():
            for dep_id in task_info['dependencies']:
                if dep_id in graph:
                    graph[dep_id]['dependents'].add(task_id)
        
        return graph
    
    async def _execute_task_graph(self, execution: WorkflowExecution, task_graph: Dict[str, Dict[str, Any]]):
        """Execute tasks based on dependency graph."""
        
        while True:
            # Find ready tasks (no pending dependencies)
            ready_tasks = [
                task_id for task_id, task_info in task_graph.items()
                if (task_info['status'] == 'pending' and 
                    not any(task_graph[dep_id]['status'] != 'completed' for dep_id in task_info['dependencies']))
            ]
            
            if not ready_tasks:
                # Check if we're done or stuck
                pending_tasks = [task_id for task_id, task_info in task_graph.items() if task_info['status'] == 'pending']
                if not pending_tasks:
                    break  # All tasks completed
                else:
                    logger.error(f"Workflow {execution.execution_id} is stuck with pending tasks: {pending_tasks}")
                    break
            
            # Execute ready tasks in parallel
            task_coroutines = []
            for task_id in ready_tasks:
                task_graph[task_id]['status'] = 'running'
                execution.current_tasks.append(task_id)
                
                coroutine = self._execute_single_task(execution, task_graph[task_id]['task'], task_graph)
                task_coroutines.append((task_id, coroutine))
            
            # Wait for all ready tasks to complete
            for task_id, coroutine in task_coroutines:
                try:
                    result = await coroutine
                    task_graph[task_id]['status'] = 'completed'
                    execution.task_results[task_id] = result
                    execution.completed_tasks.append(task_id)
                    
                    if task_id in execution.current_tasks:
                        execution.current_tasks.remove(task_id)
                    
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    task_graph[task_id]['status'] = 'failed'
                    execution.failed_tasks.append(task_id)
                    execution.task_results[task_id] = {'error': str(e)}
                    
                    if task_id in execution.current_tasks:
                        execution.current_tasks.remove(task_id)
                    
                    # Handle failure strategy
                    if execution.definition.failure_strategy == 'abort':
                        logger.info(f"Aborting workflow {execution.execution_id} due to task failure")
                        return
            
            # Update progress
            total_tasks = len(task_graph)
            completed_tasks = len(execution.completed_tasks) + len(execution.failed_tasks)
            execution.progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0
    
    async def _execute_single_task(self, execution: WorkflowExecution, task: WorkflowTask, 
                                 task_graph: Dict[str, Dict[str, Any]]) -> Any:
        """Execute a single task."""
        logger.info(f"Executing task {task.task_id} in workflow {execution.execution_id}")
        
        # Resolve parameters with results from previous tasks
        resolved_params = self._resolve_task_parameters(task.parameters, execution.task_results)
        
        # Get agent for this task
        if task.agent_role not in self.agent_registry:
            raise ValueError(f"No agent registered for role {task.agent_role}")
        
        agent = self.agent_registry[task.agent_role]
        
        # Execute task with retry logic
        last_exception = None
        for attempt in range(task.retry_count + 1):
            try:
                # Execute task action
                if hasattr(agent, task.action):
                    action_method = getattr(agent, task.action)
                    
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        action_method(**resolved_params),
                        timeout=task.timeout
                    )
                    
                    logger.info(f"Task {task.task_id} completed successfully")
                    return result
                    
                else:
                    raise AttributeError(f"Agent {task.agent_role} does not have action {task.action}")
                    
            except asyncio.TimeoutError:
                last_exception = f"Task {task.task_id} timed out after {task.timeout}s"
                logger.warning(f"Attempt {attempt + 1} failed: {last_exception}")
                
            except Exception as e:
                last_exception = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_exception}")
                
            # Wait before retry
            if attempt < task.retry_count:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        raise Exception(f"Task {task.task_id} failed after {task.retry_count + 1} attempts: {last_exception}")
    
    def _resolve_task_parameters(self, parameters: Dict[str, Any], task_results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter references to previous task results."""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                # Parameter reference
                ref = value[1:-1]  # Remove braces
                
                if '.' in ref:
                    # Nested reference like {task_id.result.field}
                    parts = ref.split('.')
                    task_id = parts[0]
                    
                    if task_id in task_results:
                        result = task_results[task_id]
                        
                        # Navigate nested structure
                        for part in parts[1:]:
                            if isinstance(result, dict) and part in result:
                                result = result[part]
                            elif hasattr(result, part):
                                result = getattr(result, part)
                            else:
                                result = None
                                break
                        
                        resolved[key] = result
                    else:
                        resolved[key] = None
                else:
                    # Simple reference like {task_id}
                    resolved[key] = task_results.get(ref)
            else:
                resolved[key] = value
        
        return resolved
    
    def register_agent(self, role: AgentRole, agent):
        """Register an agent for a specific role."""
        self.agent_registry[role] = agent
        logger.info(f"Registered agent for role {role.value}")
    
    def create_workflow(self, name: str, description: str, tasks: List[WorkflowTask],
                       global_timeout: float = 600.0, max_retries: int = 1,
                       failure_strategy: str = "abort") -> WorkflowDefinition:
        """Create a new workflow definition."""
        
        workflow_id = f"custom_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        workflow_def = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            tasks=tasks,
            global_timeout=global_timeout,
            max_retries=max_retries,
            failure_strategy=failure_strategy,
            metadata={'created_at': time.time(), 'custom': True}
        )
        
        self.workflow_definitions[name] = workflow_def
        logger.info(f"Created custom workflow: {name}")
        
        return workflow_def
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """Pause a running workflow."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.PAUSED
                logger.info(f"Paused workflow execution {execution_id}")
                return True
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """Resume a paused workflow."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            if execution.status == WorkflowStatus.PAUSED:
                execution.status = WorkflowStatus.RUNNING
                await self.execution_queue.put(execution_id)
                logger.info(f"Resumed workflow execution {execution_id}")
                return True
        return False
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a workflow execution."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = time.time()
            logger.info(f"Cancelled workflow execution {execution_id}")
            return True
        return False
    
    async def _metrics_collection_loop(self):
        """Background loop for metrics collection."""
        while self.is_running:
            try:
                if self.metrics['total_workflows'] > 0:
                    logger.info(f"Orchestration Agent Metrics - "
                              f"Total Workflows: {self.metrics['total_workflows']}, "
                              f"Success Rate: {self.metrics['success_rate']:.2%}, "
                              f"Avg Execution Time: {self.metrics['average_execution_time']:.2f}s, "
                              f"Active Executions: {len(self.active_executions)}")
                
                await asyncio.sleep(300)  # Log every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_management_loop(self):
        """Background loop for cleanup management."""
        while self.is_running:
            try:
                # Clean up old executions from history
                current_time = time.time()
                max_age = 86400  # 24 hours
                
                # Convert deque to list for iteration
                history_list = list(self.execution_history)
                cleaned_count = 0
                
                for execution in history_list:
                    if execution.end_time and (current_time - execution.end_time) > max_age:
                        try:
                            self.execution_history.remove(execution)
                            cleaned_count += 1
                        except ValueError:
                            pass  # Already removed
                
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} old workflow executions")
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup management: {e}")
                await asyncio.sleep(3600)
    
    async def _health_monitoring_loop(self):
        """Background loop for health monitoring."""
        while self.is_running:
            try:
                # Monitor active executions for timeouts
                current_time = time.time()
                
                for execution_id, execution in list(self.active_executions.items()):
                    if execution.status == WorkflowStatus.RUNNING:
                        runtime = current_time - execution.start_time
                        
                        if runtime > execution.definition.global_timeout:
                            logger.warning(f"Workflow {execution_id} exceeded global timeout")
                            execution.status = WorkflowStatus.FAILED
                            execution.end_time = current_time
                            execution.metadata['timeout'] = True
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _load_workflow_definitions(self):
        """Load workflow definitions from storage."""
        try:
            # Initialize default workflow definitions
            self.workflow_definitions = {
                'simple_query': {
                    'steps': [
                        {'agent': 'triage', 'action': 'classify'},
                        {'agent': 'research', 'action': 'gather_info', 'condition': 'needs_research'},
                        {'agent': 'orchestration', 'action': 'synthesize_response'}
                    ],
                    'conditions': {
                        'needs_research': lambda ctx: ctx.get('classification', {}).get('type') in ['information', 'research']
                    }
                },
                'complex_analysis': {
                    'steps': [
                        {'agent': 'triage', 'action': 'classify'},
                        {'agent': 'research', 'action': 'deep_research'},
                        {'agent': 'research', 'action': 'analyze_findings'},
                        {'agent': 'orchestration', 'action': 'create_report'}
                    ],
                    'parallel_steps': [
                        [{'agent': 'research', 'action': 'search_sources'}],
                        [{'agent': 'research', 'action': 'validate_information'}]
                    ]
                },
                'urgent_response': {
                    'steps': [
                        {'agent': 'triage', 'action': 'priority_classify'},
                        {'agent': 'orchestration', 'action': 'immediate_response'}
                    ],
                    'timeout': 30,  # seconds
                    'priority': 'high'
                },
                'multi_agent_collaboration': {
                    'steps': [
                        {'agent': 'triage', 'action': 'classify'},
                        {'agent': 'research', 'action': 'parallel_research', 'parallel': True},
                        {'agent': 'orchestration', 'action': 'coordinate_results'},
                        {'agent': 'orchestration', 'action': 'final_synthesis'}
                    ]
                }
            }
            
            # Load custom workflows if available
            workflows_file = self.config.data_dir / "workflows.json"
            if workflows_file.exists():
                with open(workflows_file, 'r') as f:
                    custom_workflows = json.load(f)
                    self.workflow_definitions.update(custom_workflows)
                    
            logger.info(f"Loaded {len(self.workflow_definitions)} workflow definitions")
            
        except Exception as e:
            logger.error(f"Error loading workflow definitions: {e}")
            self.workflow_definitions = {}
    
    async def _initialize_execution_engine(self):
        """Initialize the workflow execution engine."""
        try:
            # Initialize execution engine components
            self.execution_engine = {
                'active_workflows': {},
                'workflow_queue': asyncio.Queue(),
                'result_cache': {},
                'performance_metrics': {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'average_execution_time': 0.0
                },
                'resource_limits': {
                    'max_concurrent_workflows': 10,
                    'max_execution_time': 300,  # 5 minutes
                    'memory_limit_mb': 1024
                }
            }
            
            # Initialize workflow execution context
            self.execution_context = {
                'shared_data': {},
                'agent_connections': {
                    'triage': self.triage_agent,
                    'research': self.research_agent,
                    'orchestration': self
                },
                'execution_history': deque(maxlen=1000)
            }
            
            # Start execution engine background tasks
            self.execution_tasks = []
            
            logger.info("Workflow execution engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing execution engine: {e}")
            self.execution_engine = {}
    
    async def _save_execution_history(self):
        """Save execution history to persistent storage."""
        try:
            if not hasattr(self, 'execution_context') or not self.execution_context.get('execution_history'):
                return
                
            history_file = self.config.data_dir / "orchestration_history.json"
            
            # Prepare execution history for saving
            history_data = []
            for execution in list(self.execution_context['execution_history'])[-100:]:  # Keep last 100
                history_item = {
                    'workflow_id': execution.get('workflow_id', ''),
                    'workflow_type': execution.get('workflow_type', ''),
                    'start_time': execution.get('start_time', 0),
                    'end_time': execution.get('end_time', 0),
                    'duration': execution.get('duration', 0),
                    'status': execution.get('status', 'unknown'),
                    'steps_completed': len(execution.get('completed_steps', [])),
                    'success': execution.get('success', False),
                    'error': execution.get('error', '')[:200] if execution.get('error') else None
                }
                history_data.append(history_item)
            
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
            # Also save performance metrics
            metrics_file = self.config.data_dir / "orchestration_metrics.json"
            if hasattr(self, 'execution_engine'):
                with open(metrics_file, 'w') as f:
                    json.dump(self.execution_engine.get('performance_metrics', {}), f, indent=2)
                    
            logger.info(f"Saved {len(history_data)} execution history records")
            
        except Exception as e:
            logger.error(f"Error saving execution history: {e}")
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            # Test basic orchestration functionality
            test_execution = await self.orchestrate(
                'information_gathering',
                {'query': 'test health check'}
            )
            
            # Wait a moment for execution to start
            await asyncio.sleep(1)
            
            if test_execution.execution_id in self.active_executions:
                # Cancel the test execution
                await self.cancel_workflow(test_execution.execution_id)
                return "healthy"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestration agent statistics."""
        return {
            'metrics': self.metrics.copy(),
            'active_executions': len(self.active_executions),
            'execution_history_size': len(self.execution_history),
            'registered_agents': list(self.agent_registry.keys()),
            'workflow_templates': list(self.workflow_templates.keys()),
            'custom_workflows': list(self.workflow_definitions.keys())
        }
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow execution."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            return {
                'execution_id': execution_id,
                'workflow_id': execution.workflow_id,
                'status': execution.status.value,
                'progress': execution.progress,
                'start_time': execution.start_time,
                'end_time': execution.end_time,
                'current_tasks': execution.current_tasks,
                'completed_tasks': execution.completed_tasks,
                'failed_tasks': execution.failed_tasks
            }
        
        # Check execution history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return {
                    'execution_id': execution_id,
                    'workflow_id': execution.workflow_id,
                    'status': execution.status.value,
                    'progress': execution.progress,
                    'start_time': execution.start_time,
                    'end_time': execution.end_time,
                    'completed_tasks': execution.completed_tasks,
                    'failed_tasks': execution.failed_tasks
                }
        
        return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows."""
        workflows = []
        
        # Add templates
        for name, workflow_def in self.workflow_templates.items():
            workflows.append({
                'name': name,
                'workflow_id': workflow_def.workflow_id,
                'description': workflow_def.description,
                'task_count': len(workflow_def.tasks),
                'type': 'template'
            })
        
        # Add custom workflows
        for name, workflow_def in self.workflow_definitions.items():
            workflows.append({
                'name': name,
                'workflow_id': workflow_def.workflow_id,
                'description': workflow_def.description,
                'task_count': len(workflow_def.tasks),
                'type': 'custom'
            })
        
        return workflows
    
    async def restart(self):
        """Restart the orchestration agent."""
        logger.info("Restarting Orchestration Agent...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()
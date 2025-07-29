"""
Dashboard Server
Web-based dashboard interface for the AI system
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
import aiohttp
from aiohttp import web, WSMsgType
import aiohttp_cors
import jinja2
import aiofiles

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class DashboardServer:
    """Web dashboard server for system monitoring and control."""
    
    def __init__(self, config: SystemConfig, orchestrator):
        self.config = config
        self.orchestrator = orchestrator
        self.app = None
        self.runner = None
        self.site = None
        self.is_running = False
        
        # WebSocket connections
        self.websocket_connections = set()
        
        # Dashboard data cache
        self.dashboard_data = {
            'system_status': {},
            'active_workflows': [],
            'recent_alerts': [],
            'performance_metrics': {},
            'last_updated': 0
        }
        
        # Update interval
        self.update_interval = 5  # seconds
        
        logger.info("Dashboard Server initialized")
    
    async def initialize(self):
        """Initialize the dashboard server."""
        logger.info("Initializing Dashboard Server...")
        
        try:
            # Create aiohttp application
            self.app = web.Application()
            
            # Setup CORS
            cors = aiohttp_cors.setup(self.app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            # Setup routes
            await self._setup_routes()
            
            # Setup static files
            await self._setup_static_files()
            
            # Setup WebSocket endpoint
            self.app.router.add_get('/ws', self._websocket_handler)
            
            # Add CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)
            
            logger.info("Dashboard Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Dashboard Server: {e}")
            raise
    
    async def start(self):
        """Start the dashboard server."""
        logger.info("Starting Dashboard Server...")
        
        try:
            # Create runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Create site
            self.site = web.TCPSite(
                self.runner,
                host=self.config.ui.dashboard_host,
                port=self.config.ui.dashboard_port
            )
            await self.site.start()
            
            # Start background tasks
            self.background_tasks = {
                'data_updater': asyncio.create_task(self._data_update_loop()),
                'websocket_broadcaster': asyncio.create_task(self._websocket_broadcast_loop())
            }
            
            self.is_running = True
            
            logger.info(f"Dashboard Server started on http://{self.config.ui.dashboard_host}:{self.config.ui.dashboard_port}")
            
        except Exception as e:
            logger.error(f"Failed to start Dashboard Server: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the dashboard server."""
        logger.info("Shutting down Dashboard Server...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task_name, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Close WebSocket connections
        for ws in self.websocket_connections.copy():
            await ws.close()
        
        # Cleanup server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        logger.info("Dashboard Server shutdown complete")
    
    async def _setup_routes(self):
        """Setup HTTP routes."""
        # Main dashboard
        self.app.router.add_get('/', self._dashboard_handler)
        self.app.router.add_get('/dashboard', self._dashboard_handler)
        
        # API endpoints
        self.app.router.add_get('/api/status', self._api_status_handler)
        self.app.router.add_get('/api/system', self._api_system_handler)
        self.app.router.add_get('/api/workflows', self._api_workflows_handler)
        self.app.router.add_get('/api/agents', self._api_agents_handler)
        self.app.router.add_get('/api/monitoring', self._api_monitoring_handler)
        self.app.router.add_get('/api/security', self._api_security_handler)
        
        # Control endpoints
        self.app.router.add_post('/api/workflow/start', self._api_workflow_start_handler)
        self.app.router.add_post('/api/workflow/stop', self._api_workflow_stop_handler)
        self.app.router.add_post('/api/system/restart', self._api_system_restart_handler)
        
        # Health check
        self.app.router.add_get('/health', self._health_handler)
    
    async def _setup_static_files(self):
        """Setup static file serving."""
        # Create static directory if it doesn't exist
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        # Create basic HTML template
        await self._create_dashboard_template()
        
        # Serve static files
        self.app.router.add_static('/static/', path=static_dir, name='static')
    
    async def _create_dashboard_template(self):
        """Create the main dashboard HTML template."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI System Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 300;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4caf50;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .container {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #64b5f6;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-weight: bold;
            color: #81c784;
        }
        
        .alert {
            background: rgba(244, 67, 54, 0.2);
            border-left: 4px solid #f44336;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 5px;
        }
        
        .workflow-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
        }
        
        .workflow-status {
            display: inline-block;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-running { background: #4caf50; }
        .status-completed { background: #2196f3; }
        .status-failed { background: #f44336; }
        
        .btn {
            background: linear-gradient(45deg, #2196f3, #21cbf3);
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 0.5rem;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #4caf50, #81c784);
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .logs {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            height: 200px;
            overflow-y: auto;
            margin-top: 1rem;
        }
        
        .log-entry {
            margin-bottom: 0.5rem;
            opacity: 0.8;
        }
        
        .log-timestamp {
            color: #64b5f6;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
        }
        
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 4px solid #ffffff;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI System Dashboard</h1>
        <div class="status-indicator">
            <div class="status-dot" id="statusDot"></div>
            <span id="systemStatus">Connected</span>
        </div>
    </div>
    
    <div class="container">
        <div class="dashboard-grid">
            <!-- System Overview -->
            <div class="card">
                <h3>System Overview</h3>
                <div id="systemOverview">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading system data...</p>
                    </div>
                </div>
            </div>
            
            <!-- Performance Metrics -->
            <div class="card">
                <h3>Performance Metrics</h3>
                <div id="performanceMetrics">
                    <div class="metric">
                        <span>CPU Usage:</span>
                        <span class="metric-value" id="cpuUsage">0%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="cpuProgress" style="width: 0%"></div>
                    </div>
                    
                    <div class="metric">
                        <span>Memory Usage:</span>
                        <span class="metric-value" id="memoryUsage">0%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="memoryProgress" style="width: 0%"></div>
                    </div>
                    
                    <div class="metric">
                        <span>Active Workflows:</span>
                        <span class="metric-value" id="activeWorkflows">0</span>
                    </div>
                </div>
            </div>
            
            <!-- Active Workflows -->
            <div class="card">
                <h3>Active Workflows</h3>
                <div id="workflowsList">
                    <p>No active workflows</p>
                </div>
                <button class="btn" onclick="startWorkflow()">Start New Workflow</button>
            </div>
            
            <!-- Recent Alerts -->
            <div class="card">
                <h3>Recent Alerts</h3>
                <div id="alertsList">
                    <p>No recent alerts</p>
                </div>
            </div>
            
            <!-- Agent Status -->
            <div class="card">
                <h3>Agent Status</h3>
                <div id="agentStatus">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading agent data...</p>
                    </div>
                </div>
            </div>
            
            <!-- System Logs -->
            <div class="card">
                <h3>System Logs</h3>
                <div class="logs" id="systemLogs">
                    <div class="log-entry">
                        <span class="log-timestamp">[System]</span> Dashboard initialized
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Control Panel -->
        <div class="card">
            <h3>System Control</h3>
            <button class="btn" onclick="restartSystem()">Restart System</button>
            <button class="btn" onclick="pauseSystem()">Pause System</button>
            <button class="btn" onclick="resumeSystem()">Resume System</button>
            <button class="btn" onclick="refreshData()">Refresh Data</button>
        </div>
    </div>
    
    <script>
        // WebSocket connection
        let ws = null;
        let reconnectInterval = null;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                console.log('WebSocket connected');
                document.getElementById('systemStatus').textContent = 'Connected';
                document.getElementById('statusDot').style.background = '#4caf50';
                
                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function(event) {
                console.log('WebSocket disconnected');
                document.getElementById('systemStatus').textContent = 'Disconnected';
                document.getElementById('statusDot').style.background = '#f44336';
                
                // Attempt to reconnect
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(connectWebSocket, 5000);
                }
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            // Update system overview
            if (data.system_status) {
                updateSystemOverview(data.system_status);
            }
            
            // Update performance metrics
            if (data.performance_metrics) {
                updatePerformanceMetrics(data.performance_metrics);
            }
            
            // Update workflows
            if (data.active_workflows) {
                updateWorkflows(data.active_workflows);
            }
            
            // Update alerts
            if (data.recent_alerts) {
                updateAlerts(data.recent_alerts);
            }
            
            // Update agent status
            if (data.agent_status) {
                updateAgentStatus(data.agent_status);
            }
            
            // Add log entry
            addLogEntry(data);
        }
        
        function updateSystemOverview(systemStatus) {
            const overview = document.getElementById('systemOverview');
            overview.innerHTML = `
                <div class="metric">
                    <span>System State:</span>
                    <span class="metric-value">${systemStatus.state || 'Unknown'}</span>
                </div>
                <div class="metric">
                    <span>Uptime:</span>
                    <span class="metric-value">${formatUptime(systemStatus.uptime || 0)}</span>
                </div>
                <div class="metric">
                    <span>Components:</span>
                    <span class="metric-value">${systemStatus.active_components || 0}</span>
                </div>
                <div class="metric">
                    <span>Total Requests:</span>
                    <span class="metric-value">${systemStatus.total_requests || 0}</span>
                </div>
            `;
        }
        
        function updatePerformanceMetrics(metrics) {
            document.getElementById('cpuUsage').textContent = `${Math.round(metrics.cpu_usage || 0)}%`;
            document.getElementById('cpuProgress').style.width = `${metrics.cpu_usage || 0}%`;
            
            document.getElementById('memoryUsage').textContent = `${Math.round(metrics.memory_usage || 0)}%`;
            document.getElementById('memoryProgress').style.width = `${metrics.memory_usage || 0}%`;
            
            document.getElementById('activeWorkflows').textContent = metrics.active_workflows || 0;
        }
        
        function updateWorkflows(workflows) {
            const workflowsList = document.getElementById('workflowsList');
            
            if (workflows.length === 0) {
                workflowsList.innerHTML = '<p>No active workflows</p>';
                return;
            }
            
            workflowsList.innerHTML = workflows.map(workflow => `
                <div class="workflow-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${workflow.name || workflow.id}</strong>
                            <br>
                            <small>Progress: ${Math.round(workflow.progress * 100)}%</small>
                        </div>
                        <span class="workflow-status status-${workflow.status}">${workflow.status}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${workflow.progress * 100}%"></div>
                    </div>
                </div>
            `).join('');
        }
        
        function updateAlerts(alerts) {
            const alertsList = document.getElementById('alertsList');
            
            if (alerts.length === 0) {
                alertsList.innerHTML = '<p>No recent alerts</p>';
                return;
            }
            
            alertsList.innerHTML = alerts.map(alert => `
                <div class="alert">
                    <strong>${alert.title || 'Alert'}</strong>
                    <br>
                    <small>${alert.message || 'No details available'}</small>
                    <br>
                    <small>${formatTimestamp(alert.timestamp)}</small>
                </div>
            `).join('');
        }
        
        function updateAgentStatus(agentStatus) {
            const agentStatusDiv = document.getElementById('agentStatus');
            
            const agents = Object.entries(agentStatus).map(([name, status]) => `
                <div class="metric">
                    <span>${name}:</span>
                    <span class="metric-value" style="color: ${status === 'healthy' ? '#4caf50' : '#f44336'}">${status}</span>
                </div>
            `).join('');
            
            agentStatusDiv.innerHTML = agents || '<p>No agent data available</p>';
        }
        
        function addLogEntry(data) {
            const logs = document.getElementById('systemLogs');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> Dashboard updated`;
            
            logs.appendChild(logEntry);
            logs.scrollTop = logs.scrollHeight;
            
            // Keep only last 50 entries
            while (logs.children.length > 50) {
                logs.removeChild(logs.firstChild);
            }
        }
        
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
        
        function formatTimestamp(timestamp) {
            return new Date(timestamp * 1000).toLocaleString();
        }
        
        // Control functions
        async function startWorkflow() {
            try {
                const response = await fetch('/api/workflow/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ workflow: 'information_gathering', query: 'system status' })
                });
                const result = await response.json();
                addLogEntry({ message: 'Workflow started: ' + result.execution_id });
            } catch (error) {
                console.error('Error starting workflow:', error);
            }
        }
        
        async function restartSystem() {
            if (confirm('Are you sure you want to restart the system?')) {
                try {
                    await fetch('/api/system/restart', { method: 'POST' });
                    addLogEntry({ message: 'System restart initiated' });
                } catch (error) {
                    console.error('Error restarting system:', error);
                }
            }
        }
        
        async function pauseSystem() {
            try {
                await fetch('/api/system/pause', { method: 'POST' });
                addLogEntry({ message: 'System paused' });
            } catch (error) {
                console.error('Error pausing system:', error);
            }
        }
        
        async function resumeSystem() {
            try {
                await fetch('/api/system/resume', { method: 'POST' });
                addLogEntry({ message: 'System resumed' });
            } catch (error) {
                console.error('Error resuming system:', error);
            }
        }
        
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
                addLogEntry({ message: 'Data refreshed manually' });
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            refreshData();
        });
    </script>
</body>
</html>
        """
        
        template_file = Path("templates/dashboard.html")
        template_file.parent.mkdir(exist_ok=True)
        
        async with aiofiles.open(template_file, 'w') as f:
            await f.write(html_content)
    
    async def _dashboard_handler(self, request):
        """Serve the main dashboard page."""
        template_file = Path("templates/dashboard.html")
        
        if not template_file.exists():
            await self._create_dashboard_template()
        
        async with aiofiles.open(template_file, 'r') as f:
            content = await f.read()
        
        return web.Response(text=content, content_type='text/html')
    
    async def _api_status_handler(self, request):
        """API endpoint for system status."""
        try:
            status_data = await self._collect_dashboard_data()
            return web.json_response(status_data)
        except Exception as e:
            logger.error(f"Error in status API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _api_system_handler(self, request):
        """API endpoint for system information."""
        try:
            system_data = self.orchestrator.get_system_status()
            return web.json_response(system_data)
        except Exception as e:
            logger.error(f"Error in system API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _api_workflows_handler(self, request):
        """API endpoint for workflow information."""
        try:
            workflows_data = self.orchestrator.get_statistics()
            return web.json_response(workflows_data)
        except Exception as e:
            logger.error(f"Error in workflows API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _api_agents_handler(self, request):
        """API endpoint for agent information."""
        try:
            agents_data = {}
            
            # Get agent health status
            for agent_name, agent in [
                ('triage', getattr(self.orchestrator, 'triage_agent', None)),
                ('research', getattr(self.orchestrator, 'research_agent', None)),
                ('orchestration', getattr(self.orchestrator, 'orchestration_agent', None))
            ]:
                if agent and hasattr(agent, 'health_check'):
                    try:
                        health = await agent.health_check()
                        agents_data[agent_name] = health
                    except Exception:
                        agents_data[agent_name] = 'unknown'
                else:
                    agents_data[agent_name] = 'not_available'
            
            return web.json_response(agents_data)
        except Exception as e:
            logger.error(f"Error in agents API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _api_monitoring_handler(self, request):
        """API endpoint for monitoring information."""
        try:
            monitoring_data = {}
            
            # Get system monitor data if available
            if hasattr(self.orchestrator, 'components') and 'system_monitor' in self.orchestrator.components:
                system_monitor = self.orchestrator.components['system_monitor']
                monitoring_data = system_monitor.get_system_status()
            
            return web.json_response(monitoring_data)
        except Exception as e:
            logger.error(f"Error in monitoring API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _api_security_handler(self, request):
        """API endpoint for security information."""
        try:
            security_data = {}
            
            # Get security monitor data if available
            if hasattr(self.orchestrator, 'components') and 'security_monitor' in self.orchestrator.components:
                security_monitor = self.orchestrator.components['security_monitor']
                security_data = security_monitor.get_security_status()
            
            return web.json_response(security_data)
        except Exception as e:
            logger.error(f"Error in security API: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _api_workflow_start_handler(self, request):
        """API endpoint to start a workflow."""
        try:
            data = await request.json()
            workflow_name = data.get('workflow', 'information_gathering')
            parameters = data.get('parameters', {})
            
            execution = await self.orchestrator.orchestrate(workflow_name, parameters)
            
            return web.json_response({
                'success': True,
                'execution_id': execution.execution_id,
                'workflow_id': execution.workflow_id
            })
        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            return web.json_response({'success': False, 'error': str(e)}, status=500)
    
    async def _api_workflow_stop_handler(self, request):
        """API endpoint to stop a workflow."""
        try:
            data = await request.json()
            execution_id = data.get('execution_id')
            
            if not execution_id:
                return web.json_response({'success': False, 'error': 'execution_id required'}, status=400)
            
            success = await self.orchestrator.cancel_workflow(execution_id)
            
            return web.json_response({'success': success})
        except Exception as e:
            logger.error(f"Error stopping workflow: {e}")
            return web.json_response({'success': False, 'error': str(e)}, status=500)
    
    async def _api_system_restart_handler(self, request):
        """API endpoint to restart the system."""
        try:
            # This would trigger a system restart
            logger.info("System restart requested via API")
            
            # In a real implementation, this might trigger a graceful restart
            return web.json_response({'success': True, 'message': 'Restart initiated'})
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            return web.json_response({'success': False, 'error': str(e)}, status=500)
    
    async def _health_handler(self, request):
        """Health check endpoint."""
        try:
            health_status = await self.health_check()
            return web.json_response({
                'status': health_status,
                'timestamp': time.time(),
                'version': '1.0.0'
            })
        except Exception as e:
            return web.json_response({'status': 'unhealthy', 'error': str(e)}, status=500)
    
    async def _websocket_handler(self, request):
        """WebSocket handler for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_connections.add(ws)
        logger.info("New WebSocket connection established")
        
        try:
            # Send initial data
            initial_data = await self._collect_dashboard_data()
            await ws.send_str(json.dumps(initial_data))
            
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # Handle WebSocket commands if needed
                        if data.get('command') == 'refresh':
                            dashboard_data = await self._collect_dashboard_data()
                            await ws.send_str(json.dumps(dashboard_data))
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON received from WebSocket")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)
            logger.info("WebSocket connection closed")
        
        return ws
    
    async def _data_update_loop(self):
        """Background loop to update dashboard data."""
        while self.is_running:
            try:
                # Collect fresh data
                self.dashboard_data = await self._collect_dashboard_data()
                self.dashboard_data['last_updated'] = time.time()
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data update loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _websocket_broadcast_loop(self):
        """Background loop to broadcast updates to WebSocket clients."""
        while self.is_running:
            try:
                if self.websocket_connections and self.dashboard_data:
                    # Broadcast to all connected clients
                    message = json.dumps(self.dashboard_data)
                    
                    for ws in self.websocket_connections.copy():
                        try:
                            await ws.send_str(message)
                        except Exception as e:
                            logger.warning(f"Error sending to WebSocket: {e}")
                            self.websocket_connections.discard(ws)
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket broadcast loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _collect_dashboard_data(self) -> Dict[str, Any]:
        """Collect all dashboard data from various sources."""
        try:
            dashboard_data = {
                'timestamp': time.time(),
                'system_status': {},
                'performance_metrics': {},
                'active_workflows': [],
                'recent_alerts': [],
                'agent_status': {}
            }
            
            # Get system status
            try:
                dashboard_data['system_status'] = self.orchestrator.get_system_status()
            except Exception as e:
                logger.warning(f"Could not get system status: {e}")
            
            # Get performance metrics
            try:
                if hasattr(self.orchestrator, 'components') and 'system_monitor' in self.orchestrator.components:
                    system_monitor = self.orchestrator.components['system_monitor']
                    monitor_status = system_monitor.get_system_status()
                    
                    dashboard_data['performance_metrics'] = {
                        'cpu_usage': monitor_status.get('system_summary', {}).get('cpu_usage', 0),
                        'memory_usage': monitor_status.get('system_summary', {}).get('memory_usage', 0),
                        'disk_usage': monitor_status.get('system_summary', {}).get('disk_usage', 0),
                        'active_workflows': len(self.orchestrator.active_executions) if hasattr(self.orchestrator, 'active_executions') else 0
                    }
            except Exception as e:
                logger.warning(f"Could not get performance metrics: {e}")
            
            # Get active workflows
            try:
                if hasattr(self.orchestrator, 'active_executions'):
                    dashboard_data['active_workflows'] = [
                        {
                            'id': execution.execution_id,
                            'name': execution.definition.name,
                            'status': execution.status.value,
                            'progress': execution.progress,
                            'start_time': execution.start_time
                        }
                        for execution in self.orchestrator.active_executions.values()
                    ]
            except Exception as e:
                logger.warning(f"Could not get active workflows: {e}")
            
            # Get recent alerts
            try:
                if hasattr(self.orchestrator, 'components') and 'system_monitor' in self.orchestrator.components:
                    system_monitor = self.orchestrator.components['system_monitor']
                    monitor_status = system_monitor.get_system_status()
                    dashboard_data['recent_alerts'] = monitor_status.get('active_alerts', [])[:5]  # Last 5 alerts
            except Exception as e:
                logger.warning(f"Could not get recent alerts: {e}")
            
            # Get agent status
            try:
                agents = ['triage_agent', 'research_agent', 'orchestration_agent']
                for agent_name in agents:
                    if hasattr(self.orchestrator, agent_name):
                        agent = getattr(self.orchestrator, agent_name)
                        if hasattr(agent, 'health_check'):
                            try:
                                health = await agent.health_check()
                                dashboard_data['agent_status'][agent_name] = health
                            except Exception:
                                dashboard_data['agent_status'][agent_name] = 'unknown'
            except Exception as e:
                logger.warning(f"Could not get agent status: {e}")
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error collecting dashboard data: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e),
                'system_status': {},
                'performance_metrics': {},
                'active_workflows': [],
                'recent_alerts': [],
                'agent_status': {}
            }
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            if not self.is_running:
                return "unhealthy"
            
            # Check if server is responding
            if self.app and self.runner:
                return "healthy"
            else:
                return "degraded"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dashboard server statistics."""
        return {
            'is_running': self.is_running,
            'websocket_connections': len(self.websocket_connections),
            'last_data_update': self.dashboard_data.get('last_updated', 0),
            'dashboard_port': self.config.ui.dashboard_port
        }
    
    async def restart(self):
        """Restart the dashboard server."""
        logger.info("Restarting Dashboard Server...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()
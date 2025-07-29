"""
Web Admin Panel for IGED
Remote control and monitoring interface
"""

import threading
import time
import json
from datetime import datetime
import logging

# Try to import Flask dependencies
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Flask not available: {e}")
    FLASK_AVAILABLE = False
    # Create dummy classes for type hints
    class Flask:
        def __init__(self, *args, **kwargs):
            pass
    def render_template(*args, **kwargs):
        return ""
    def request():
        pass
    def jsonify(*args, **kwargs):
        return {}
    def redirect(*args, **kwargs):
        return ""
    def url_for(*args, **kwargs):
        return ""
    class CORS:
        def __init__(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)

class WebAdminPanel:
    def __init__(self, components):
        self.components = components
        
        # Check if Flask is available
        if not FLASK_AVAILABLE:
            logger.warning("⚠️ Flask not available, web admin panel disabled")
            self.app = None
            self.server_thread = None
            self.running = False
            return
        
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'iged-secret-key-2024'
        CORS(self.app)
        
        self.setup_routes()
        self.server_thread = None
        self.running = False
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status"""
            try:
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'system': 'IGED',
                    'version': '1.0.0'
                }
                
                # Voice pipeline status
                if 'voice' in self.components:
                    voice_status = self.components['voice'].get_status()
                    status['voice'] = voice_status
                
                # Orchestrator status
                if 'orchestrator' in self.components:
                    orch_status = self.components['orchestrator'].get_system_status()
                    status['orchestrator'] = orch_status
                
                # Memory status
                if 'memory' in self.components:
                    memory_stats = self.components['memory'].get_statistics()
                    status['memory'] = memory_stats
                
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/execute', methods=['POST'])
        def execute_command():
            """Execute a command"""
            try:
                data = request.get_json()
                command = data.get('command', '').strip()
                
                if not command:
                    return jsonify({'error': 'No command provided'}), 400
                
                # Execute command
                if 'voice' in self.components:
                    self.components['voice'].process_text_command(command)
                    return jsonify({'message': 'Command executed', 'command': command})
                else:
                    return jsonify({'error': 'Voice pipeline not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory')
        def get_memory():
            """Get memory entries"""
            try:
                limit = request.args.get('limit', 50, type=int)
                
                if 'memory' in self.components:
                    entries = self.components['memory'].get_recent_entries(limit)
                    return jsonify({'entries': entries})
                else:
                    return jsonify({'error': 'Memory not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/search')
        def search_memory():
            """Search memory entries"""
            try:
                query = request.args.get('q', '').strip()
                limit = request.args.get('limit', 20, type=int)
                
                if not query:
                    return jsonify({'error': 'No search query provided'}), 400
                
                if 'memory' in self.components:
                    entries = self.components['memory'].search_entries(query, limit)
                    return jsonify({'entries': entries, 'query': query})
                else:
                    return jsonify({'error': 'Memory not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/agents')
        def get_agents():
            """Get available agents"""
            try:
                if 'orchestrator' in self.components:
                    agents = self.components['orchestrator'].get_available_agents()
                    plugins = self.components['orchestrator'].get_available_plugins()
                    
                    return jsonify({
                        'agents': agents,
                        'plugins': plugins
                    })
                else:
                    return jsonify({'error': 'Orchestrator not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/voice/toggle', methods=['POST'])
        def toggle_voice():
            """Toggle voice listening"""
            try:
                if 'voice' in self.components:
                    voice = self.components['voice']
                    if voice.is_listening:
                        voice.stop_listening()
                        return jsonify({'message': 'Voice stopped', 'listening': False})
                    else:
                        voice.start_listening()
                        return jsonify({'message': 'Voice started', 'listening': True})
                else:
                    return jsonify({'error': 'Voice pipeline not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/clear', methods=['POST'])
        def clear_memory():
            """Clear all memory"""
            try:
                if 'memory' in self.components:
                    self.components['memory'].clear_memory()
                    return jsonify({'message': 'Memory cleared'})
                else:
                    return jsonify({'error': 'Memory not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/export', methods=['POST'])
        def export_memory():
            """Export memory"""
            try:
                data = request.get_json()
                filename = data.get('filename', f'memory_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                
                if 'memory' in self.components:
                    success = self.components['memory'].export_memory(filename)
                    if success:
                        return jsonify({'message': 'Memory exported', 'filename': filename})
                    else:
                        return jsonify({'error': 'Export failed'}), 500
                else:
                    return jsonify({'error': 'Memory not available'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start(self):
        """Start the web admin server"""
        if self.running:
            logger.warning("Web admin already running")
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info("🌐 Web admin panel started on http://localhost:8080")
    
    def stop(self):
        """Stop the web admin server"""
        self.running = False
        logger.info("🛑 Web admin panel stopped")
    
    def _run_server(self):
        """Run the Flask server"""
        try:
            self.app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Web admin server error: {e}")
    
    def get_status(self) -> dict:
        """Get web admin status"""
        return {
            'running': self.running,
            'port': 8080,
            'url': 'http://localhost:8080'
        } 
"""
Orchestrator for IGED
Manages and delegates tasks to different agents
"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, memory_engine):
        self.memory = memory_engine
        self.agents = {}
        self.plugins = {}
        self.load_agents()
        self.load_plugins()
    
    def load_agents(self):
        """Load all available agents"""
        try:
            agents_dir = Path("agents")
            if not agents_dir.exists():
                agents_dir.mkdir(parents=True, exist_ok=True)
            
            # Load built-in agents
            self._load_agent("codegen_agent", "CodeGenAgent")
            self._load_agent("secops", "SecOpsAgent")
            self._load_agent("data_miner", "DataMinerAgent")
            
            # Load advanced security agents
            self._load_agent("advanced_secops", "AdvancedSecOpsAgent")
            self._load_agent("network_intelligence", "NetworkIntelligenceAgent")
            self._load_agent("remote_control", "RemoteControlAgent")
            
            logger.info(f"✅ Loaded {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"❌ Failed to load agents: {e}")
    
    def _load_agent(self, agent_name: str, class_name: str):
        """Load a specific agent"""
        try:
            # Try to import agent module
            module_path = f"agents.{agent_name}.main"
            agent_module = importlib.import_module(module_path)
            agent_class = getattr(agent_module, class_name)
            
            # Initialize agent
            agent_instance = agent_class(self.memory)
            self.agents[agent_name] = agent_instance
            
            logger.info(f"🤖 Loaded agent: {agent_name}")
            
        except ImportError:
            logger.warning(f"⚠️ Agent not found: {agent_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load agent {agent_name}: {e}")
    
    def load_plugins(self):
        """Load all available plugins"""
        try:
            plugins_dir = Path("plugins")
            if not plugins_dir.exists():
                plugins_dir.mkdir(parents=True, exist_ok=True)
            
            # Load Python plugins
            for plugin_file in plugins_dir.glob("*.py"):
                if plugin_file.name != "__init__.py":
                    self._load_plugin(plugin_file)
            
            logger.info(f"✅ Loaded {len(self.plugins)} plugins")
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugins: {e}")
    
    def _load_plugin(self, plugin_file: Path):
        """Load a specific plugin"""
        try:
            plugin_name = plugin_file.stem
            
            # Import plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if spec is None or spec.loader is None:
                logger.error(f"❌ Failed to create spec for plugin: {plugin_name}")
                return
                
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            
            # Get Plugin class
            if hasattr(plugin_module, 'Plugin'):
                plugin_instance = plugin_module.Plugin()
                self.plugins[plugin_name] = plugin_instance
                logger.info(f"🔌 Loaded plugin: {plugin_name}")
            else:
                logger.warning(f"⚠️ Plugin {plugin_name} missing Plugin class")
                
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {plugin_file.name}: {e}")
    
    def execute_command(self, command: Dict[str, Any]) -> str:
        """Execute a parsed command"""
        try:
            command_type = command.get('command_type', 'unknown')
            target = command.get('target', '')
            agent = command.get('agent', 'unknown')
            parameters = command.get('parameters', {})
            
            logger.info(f"🎯 Executing command: {command_type} -> {agent}")
            
            # Try agent first
            if agent in self.agents:
                result = self.agents[agent].execute(target, parameters)
                return result
            
            # Try plugins
            for plugin_name, plugin in self.plugins.items():
                if self._plugin_matches(plugin_name, command_type, target):
                    result = plugin.run(target)
                    return result
            
            # Fallback to general agent
            if 'general' in self.agents:
                result = self.agents['general'].execute(target, parameters)
                return result
            
            # No handler found
            return f"❌ No agent or plugin found to handle: {command_type}"
            
        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return f"❌ Execution error: {str(e)}"
    
    def _plugin_matches(self, plugin_name: str, command_type: str, target: str) -> bool:
        """Check if plugin should handle this command"""
        # Simple matching logic - can be enhanced
        target_lower = target.lower()
        plugin_lower = plugin_name.lower()
        
        return (plugin_lower in target_lower or 
                target_lower in plugin_lower or
                command_type in plugin_lower)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents"""
        return list(self.agents.keys())
    
    def get_available_plugins(self) -> List[str]:
        """Get list of available plugins"""
        return list(self.plugins.keys())
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of specific agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if hasattr(agent, 'get_status'):
                return agent.get_status()
            else:
                return {'status': 'active', 'agent': agent_name}
        return {'status': 'not_found', 'agent': agent_name}
    
    def reload_agent(self, agent_name: str) -> bool:
        """Reload a specific agent"""
        try:
            if agent_name in self.agents:
                del self.agents[agent_name]
            
            self._load_agent(agent_name, f"{agent_name.title()}Agent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reload agent {agent_name}: {e}")
            return False
    
    def reload_plugins(self) -> bool:
        """Reload all plugins"""
        try:
            self.plugins.clear()
            self.load_plugins()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reload plugins: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'agents': {
                name: self.get_agent_status(name) 
                for name in self.get_available_agents()
            },
            'plugins': self.get_available_plugins(),
            'total_agents': len(self.agents),
            'total_plugins': len(self.plugins)
        } 
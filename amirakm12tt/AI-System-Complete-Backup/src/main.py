#!/usr/bin/env python3
"""
AI System: Main Entry Point
Comprehensive Multi-Agent Architecture with Kernel Integration
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

# Import uvloop with fallback
try:
    import uvloop
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False
    logging.getLogger(__name__).warning("uvloop not available, falling back to standard asyncio")

# Import core system components
from .core.orchestrator import SystemOrchestrator
from .core.config import SystemConfig
from .kernel.integration import KernelManager
from .sensors.fusion import SensorFusionManager
from .ai.rag_engine import RAGEngine
from .ai.speculative_decoder import SpeculativeDecoder
from .agents.triage_agent import TriageAgent
from .agents.research_agent import ResearchAgent
from .agents.orchestration_agent import OrchestrationAgent
from .ui.dashboard import DashboardServer
from .ui.voice_interface import VoiceInterface
from .monitoring.system_monitor import SystemMonitor
from .monitoring.security_monitor import SecurityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AISystem:
    """Main AI System class that orchestrates all components."""
    
    def __init__(self):
        self.config = SystemConfig()
        self.running = False
        self.components = {}
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
    async def initialize_components(self):
        """Initialize all system components in proper order."""
        logger.info("Initializing AI System components...")
        
        try:
            # 1. Initialize monitoring first
            self.components['system_monitor'] = SystemMonitor(self.config)
            self.components['security_monitor'] = SecurityMonitor(self.config)
            
            # 2. Initialize kernel-level integration
            self.components['kernel_manager'] = KernelManager(self.config)
            await self.components['kernel_manager'].initialize()
            
            # 3. Initialize sensor fusion
            self.components['sensor_fusion'] = SensorFusionManager(self.config)
            await self.components['sensor_fusion'].initialize()
            
            # 4. Initialize AI engines
            self.components['rag_engine'] = RAGEngine(self.config)
            await self.components['rag_engine'].initialize()
            
            self.components['speculative_decoder'] = SpeculativeDecoder(self.config)
            await self.components['speculative_decoder'].initialize()
            
            # 5. Initialize AI agents
            self.components['triage_agent'] = TriageAgent(
                self.config,
                self.components['rag_engine'],
                self.components['speculative_decoder']
            )
            
            self.components['research_agent'] = ResearchAgent(
                self.config,
                self.components['rag_engine'],
                self.components['speculative_decoder']
            )
            
            self.components['orchestration_agent'] = OrchestrationAgent(
                self.config,
                self.components['triage_agent'],
                self.components['research_agent']
            )
            
            # 6. Initialize system orchestrator
            self.components['orchestrator'] = SystemOrchestrator(
                self.config,
                self.components
            )
            
            # 7. Initialize user interfaces
            self.components['dashboard'] = DashboardServer(
                self.config,
                self.components['orchestrator']
            )
            
            self.components['voice_interface'] = VoiceInterface(
                self.config,
                self.components['orchestrator']
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def start_system(self):
        """Start all system components."""
        logger.info("Starting AI System...")
        
        try:
            # Start monitoring
            await self.components['system_monitor'].start()
            await self.components['security_monitor'].start()
            
            # Start core components
            await self.components['kernel_manager'].start()
            await self.components['sensor_fusion'].start()
            await self.components['rag_engine'].start()
            await self.components['speculative_decoder'].start()
            
            # Start agents
            await self.components['triage_agent'].start()
            await self.components['research_agent'].start()
            await self.components['orchestration_agent'].start()
            
            # Start orchestrator
            await self.components['orchestrator'].start()
            
            # Start user interfaces
            await self.components['dashboard'].start()
            await self.components['voice_interface'].start()
            
            self.running = True
            logger.info("AI System started successfully")
            
            # Print system status
            await self.print_system_status()
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Gracefully shutdown all system components."""
        if not self.running:
            return
            
        logger.info("Shutting down AI System...")
        self.running = False
        
        # Shutdown in reverse order
        shutdown_order = [
            'voice_interface', 'dashboard', 'orchestrator',
            'orchestration_agent', 'research_agent', 'triage_agent',
            'speculative_decoder', 'rag_engine', 'sensor_fusion',
            'kernel_manager', 'security_monitor', 'system_monitor'
        ]
        
        for component_name in shutdown_order:
            if component_name in self.components:
                try:
                    await self.components[component_name].shutdown()
                    logger.info(f"Shutdown {component_name}")
                except Exception as e:
                    logger.error(f"Error shutting down {component_name}: {e}")
        
        logger.info("AI System shutdown complete")
    
    async def print_system_status(self):
        """Print current system status."""
        print("\n" + "="*60)
        print("AI SYSTEM STATUS")
        print("="*60)
        print(f"System Running: {self.running}")
        print(f"Components Active: {len(self.components)}")
        print("\nComponent Status:")
        for name, component in self.components.items():
            status = "ACTIVE" if hasattr(component, 'is_running') and component.is_running else "INITIALIZED"
            print(f"  {name:20} : {status}")
        
        print(f"\nDashboard URL: http://localhost:{self.config.dashboard_port}")
        print(f"Voice Interface: {'ACTIVE' if 'voice_interface' in self.components else 'INACTIVE'}")
        print("="*60)
    
    async def run_forever(self):
        """Keep the system running until interrupted."""
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # Perform health checks
                await self.health_check()
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            await self.shutdown()
    
    async def health_check(self):
        """Perform system health checks."""
        # This runs every second to monitor system health
        if hasattr(self.components.get('system_monitor'), 'perform_health_check'):
            await self.components['system_monitor'].perform_health_check()

def setup_signal_handlers(ai_system):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        if ai_system.running:
            asyncio.create_task(ai_system.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point."""
    logger.info("Starting AI System...")
    
    # Use uvloop for better performance if available
    if sys.platform != 'win32' and UVLOOP_AVAILABLE:
        uvloop.install()
    
    # Create and initialize system
    ai_system = AISystem()
    setup_signal_handlers(ai_system)
    
    try:
        await ai_system.initialize_components()
        await ai_system.start_system()
        await ai_system.run_forever()
    except Exception as e:
        logger.error(f"System startup failed: {e}")
        sys.exit(1)

def run_system():
    """Entry point for running the AI system."""
    try:
        # Set up uvloop for better performance on Unix systems if available
        if sys.platform != 'win32' and UVLOOP_AVAILABLE:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System shutdown requested by user")
    except Exception as e:
        logger.error(f"System failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Add proper path handling for direct execution
    src_path = Path(__file__).parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    run_system()
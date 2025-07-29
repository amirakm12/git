#!/usr/bin/env python3
"""
IGED - Project Human Bot Launcher
Main entry point for the sovereign AI assistant
"""

import os
import sys
import threading
import time
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.voice_pipeline import VoicePipeline
from core.command_parser import CommandParser
from core.memory_engine import MemoryEngine
from core.encryption import EncryptionManager
from agents.orchestrator import Orchestrator
from ui.win_gui.main_window import IGEDGUI
from admin_panel.web_admin import WebAdminPanel
from watchdog import Watchdog
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/iged.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class IGEDLauncher:
    def __init__(self):
        self.running = False
        self.components = {}
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize all IGED components"""
        try:
            logger.info("🚀 Initializing IGED System...")
            
            # Create necessary directories
            self.create_directories()
            
            # Initialize encryption
            self.components['encryption'] = EncryptionManager()
            
            # Initialize memory engine
            self.components['memory'] = MemoryEngine(self.components['encryption'])
            
            # Initialize command parser
            self.components['parser'] = CommandParser()
            
            # Initialize orchestrator
            self.components['orchestrator'] = Orchestrator(self.components['memory'])
            
            # Initialize voice pipeline
            self.components['voice'] = VoicePipeline(
                self.components['parser'],
                self.components['orchestrator'],
                self.components['memory']
            )
            
            # Initialize watchdog
            self.components['watchdog'] = Watchdog(self.components)
            
            logger.info("✅ System initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            raise
    
    def create_directories(self):
        """Create necessary project directories"""
        directories = [
            'config',
            'memory',
            'plugins',
            'agents',
            'ui/win_gui',
            'admin_panel',
            'android-client',
            'logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def start_gui(self):
        """Start the GUI interface"""
        try:
            logger.info("🖥️ Starting GUI interface...")
            self.components['gui'] = IGEDGUI(self.components)
            self.components['gui'].run()
        except Exception as e:
            logger.error(f"❌ Failed to start GUI: {e}")
    
    def start_web_admin(self):
        """Start the web admin panel"""
        try:
            logger.info("🌐 Starting web admin panel...")
            self.components['web_admin'] = WebAdminPanel(self.components)
            self.components['web_admin'].start()
        except Exception as e:
            logger.error(f"❌ Failed to start web admin: {e}")
    
    def start_voice_listening(self):
        """Start voice listening in background"""
        try:
            logger.info("🎤 Starting voice listening...")
            self.components['voice'].start_listening()
        except Exception as e:
            logger.error(f"❌ Failed to start voice listening: {e}")
    
    def run(self):
        """Main run loop"""
        try:
            self.running = True
            logger.info("🎯 IGED is now running!")
            
            # Start components in separate threads
            threads = []
            
            # Voice listening thread
            voice_thread = threading.Thread(target=self.start_voice_listening, daemon=True)
            voice_thread.start()
            threads.append(voice_thread)
            
            # Web admin thread
            web_thread = threading.Thread(target=self.start_web_admin, daemon=True)
            web_thread.start()
            threads.append(web_thread)
            
            # Watchdog thread
            watchdog_thread = threading.Thread(target=self.components['watchdog'].run, daemon=True)
            watchdog_thread.start()
            threads.append(watchdog_thread)
            
            # Start GUI (main thread)
            self.start_gui()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested...")
        except Exception as e:
            logger.error(f"❌ Runtime error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components"""
        logger.info("🔄 Shutting down IGED...")
        self.running = False
        
        # Stop voice listening
        if 'voice' in self.components:
            self.components['voice'].stop_listening()
        
        # Stop web admin
        if 'web_admin' in self.components:
            self.components['web_admin'].stop()
        
        # Stop watchdog
        if 'watchdog' in self.components:
            self.components['watchdog'].stop()
        
        logger.info("✅ IGED shutdown complete")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    # Check dependencies
    print("🔧 Checking dependencies...")
    missing_deps = []
    
    try:
        import cryptography
    except ImportError:
        missing_deps.append("cryptography")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    if missing_deps:
        print(f"⚠️ Missing dependencies: {', '.join(missing_deps)}")
        print("💡 Run: python install_dependencies.py")
        print("💡 Or: install_deps.bat (Windows)")
        print("\n🚀 Starting IGED anyway... (some features may not work)")
    
    # Check for required files
    if not Path("config/secret.key").exists():
        print("🔑 Generating encryption key...")
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            Path("config").mkdir(exist_ok=True)
            with open("config/secret.key", "wb") as f:
                f.write(key)
        except ImportError:
            print("❌ cryptography not available, cannot generate key")
            print("Please install: pip install cryptography")
            sys.exit(1)
    
    # Launch IGED
    try:
        launcher = IGEDLauncher()
        launcher.run()
    except Exception as e:
        print(f"❌ IGED failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
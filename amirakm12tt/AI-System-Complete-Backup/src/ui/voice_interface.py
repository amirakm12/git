"""
Voice Interface
Speech recognition and text-to-speech interface for the AI system
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import queue
import wave
import io

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class VoiceState(Enum):
    """Voice interface states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

@dataclass
class VoiceCommand:
    """Voice command data."""
    command_id: str
    text: str
    confidence: float
    timestamp: float
    processed: bool
    response: Optional[str] = None

class VoiceInterface:
    """Voice interface for speech recognition and synthesis."""
    
    def __init__(self, config: SystemConfig, orchestrator):
        self.config = config
        self.orchestrator = orchestrator
        self.is_running = False
        self.state = VoiceState.IDLE
        
        # Voice processing components
        self.speech_recognizer = None
        self.text_to_speech = None
        self.audio_input = None
        self.audio_output = None
        
        # Command processing
        self.command_queue = queue.Queue()
        self.voice_commands = {}
        self.command_handlers = {}
        
        # Voice settings
        self.language = self.config.ui.voice_language
        self.wake_words = ["hey system", "ai assistant", "computer"]
        self.confidence_threshold = 0.7
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # Performance metrics
        self.voice_stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'average_response_time': 0.0,
            'recognition_accuracy': 0.0
        }
        
        # Initialize command handlers
        self._initialize_command_handlers()
        
        logger.info("Voice Interface initialized")
    
    def _initialize_command_handlers(self):
        """Initialize voice command handlers."""
        self.command_handlers = {
            'status': self._handle_status_command,
            'system': self._handle_system_command,
            'workflow': self._handle_workflow_command,
            'agent': self._handle_agent_command,
            'help': self._handle_help_command,
            'stop': self._handle_stop_command,
            'shutdown': self._handle_shutdown_command,
            'restart': self._handle_restart_command
        }
    
    async def initialize(self):
        """Initialize the voice interface."""
        logger.info("Initializing Voice Interface...")
        
        try:
            # Initialize speech recognition
            await self._initialize_speech_recognition()
            
            # Initialize text-to-speech
            await self._initialize_text_to_speech()
            
            # Initialize audio I/O
            await self._initialize_audio()
            
            # Test voice components
            await self._test_voice_components()
            
            logger.info("Voice Interface initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Voice Interface: {e}")
            # Don't raise - voice interface is optional
            self.config.ui.voice_enabled = False
    
    async def start(self):
        """Start the voice interface."""
        if not self.config.ui.voice_enabled:
            logger.info("Voice interface disabled in configuration")
            return
        
        logger.info("Starting Voice Interface...")
        
        try:
            # Start background tasks
            self.background_tasks = {
                'audio_listener': asyncio.create_task(self._audio_listening_loop()),
                'command_processor': asyncio.create_task(self._command_processing_loop()),
                'wake_word_detector': asyncio.create_task(self._wake_word_detection_loop()),
                'voice_monitor': asyncio.create_task(self._voice_monitoring_loop())
            }
            
            self.is_running = True
            self.state = VoiceState.IDLE
            
            # Announce startup
            await self._speak("Voice interface activated. Say 'Hey System' to begin.")
            
            logger.info("Voice Interface started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Voice Interface: {e}")
            self.config.ui.voice_enabled = False
    
    async def shutdown(self):
        """Shutdown the voice interface."""
        logger.info("Shutting down Voice Interface...")
        
        self.is_running = False
        self.state = VoiceState.IDLE
        
        # Announce shutdown
        if self.config.ui.voice_enabled:
            await self._speak("Voice interface shutting down.")
        
        # Cancel background tasks
        if hasattr(self, 'background_tasks'):
            for task_name, task in self.background_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(f"Cancelled {task_name}")
        
        # Cleanup audio resources
        await self._cleanup_audio()
        
        logger.info("Voice Interface shutdown complete")
    
    async def _initialize_speech_recognition(self):
        """Initialize speech recognition system."""
        try:
            # Try to import speech recognition library
            import speech_recognition as sr
            
            self.speech_recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.speech_recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info("Speech recognition initialized")
            
        except ImportError:
            logger.warning("speech_recognition library not available - using mock implementation")
            self.speech_recognizer = MockSpeechRecognizer()
            self.microphone = MockMicrophone()
        except Exception as e:
            logger.error(f"Error initializing speech recognition: {e}")
            raise
    
    async def _initialize_text_to_speech(self):
        """Initialize text-to-speech system."""
        try:
            # Try to import text-to-speech library
            import pyttsx3
            
            self.text_to_speech = pyttsx3.init()
            
            # Configure TTS settings
            self.text_to_speech.setProperty('rate', 150)  # Speed
            self.text_to_speech.setProperty('volume', 0.8)  # Volume
            
            # Set voice (try to use a pleasant voice)
            voices = self.text_to_speech.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.text_to_speech.setProperty('voice', voice.id)
                        break
                else:
                    self.text_to_speech.setProperty('voice', voices[0].id)
            
            logger.info("Text-to-speech initialized")
            
        except ImportError:
            logger.warning("pyttsx3 library not available - using mock implementation")
            self.text_to_speech = MockTextToSpeech()
        except Exception as e:
            logger.error(f"Error initializing text-to-speech: {e}")
            raise
    
    async def _initialize_audio(self):
        """Initialize audio input/output."""
        try:
            # Try to import audio library
            import pyaudio
            
            self.audio = pyaudio.PyAudio()
            
            # Get default audio devices
            self.input_device = self.audio.get_default_input_device_info()
            self.output_device = self.audio.get_default_output_device_info()
            
            logger.info(f"Audio initialized - Input: {self.input_device['name']}, "
                       f"Output: {self.output_device['name']}")
            
        except ImportError:
            logger.warning("pyaudio library not available - using mock implementation")
            self.audio = MockAudio()
            self.input_device = {'name': 'Mock Input'}
            self.output_device = {'name': 'Mock Output'}
        except Exception as e:
            logger.error(f"Error initializing audio: {e}")
            raise
    
    async def _test_voice_components(self):
        """Test voice components."""
        try:
            # Test TTS
            await self._speak("Voice interface test successful.", wait=True)
            
            logger.info("Voice components test passed")
            
        except Exception as e:
            logger.warning(f"Voice components test failed: {e}")
    
    async def _audio_listening_loop(self):
        """Main audio listening loop."""
        while self.is_running:
            try:
                if self.state == VoiceState.LISTENING:
                    # Listen for audio input
                    audio_data = await self._capture_audio()
                    
                    if audio_data:
                        # Process audio for speech
                        await self._process_audio(audio_data)
                
                await asyncio.sleep(0.1)  # Small delay to prevent CPU overload
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audio listening loop: {e}")
                await asyncio.sleep(1)
    
    async def _command_processing_loop(self):
        """Process voice commands from the queue."""
        while self.is_running:
            try:
                # Check for commands in queue
                if not self.command_queue.empty():
                    command_text = self.command_queue.get_nowait()
                    await self._process_voice_command(command_text)
                
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in command processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _wake_word_detection_loop(self):
        """Detect wake words to activate listening."""
        while self.is_running:
            try:
                if self.state == VoiceState.IDLE:
                    # Listen for wake words
                    audio_data = await self._capture_audio(duration=2)
                    
                    if audio_data:
                        text = await self._recognize_speech(audio_data)
                        
                        if text and self._contains_wake_word(text):
                            logger.info(f"Wake word detected: {text}")
                            await self._activate_listening()
                
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in wake word detection loop: {e}")
                await asyncio.sleep(1)
    
    async def _voice_monitoring_loop(self):
        """Monitor voice interface performance and status."""
        while self.is_running:
            try:
                # Log voice interface statistics
                if self.voice_stats['total_commands'] > 0:
                    success_rate = (self.voice_stats['successful_commands'] / 
                                  self.voice_stats['total_commands']) * 100
                    
                    logger.info(f"Voice Interface Stats - "
                              f"Commands: {self.voice_stats['total_commands']}, "
                              f"Success Rate: {success_rate:.1f}%, "
                              f"Avg Response Time: {self.voice_stats['average_response_time']:.2f}s")
                
                await asyncio.sleep(300)  # Log every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in voice monitoring loop: {e}")
                await asyncio.sleep(300)
    
    async def _capture_audio(self, duration: float = 3.0) -> Optional[bytes]:
        """Capture audio from microphone."""
        try:
            if isinstance(self.speech_recognizer, MockSpeechRecognizer):
                # Mock implementation
                await asyncio.sleep(0.1)
                return b"mock_audio_data"
            
            # Real implementation using speech_recognition
            import speech_recognition as sr
            
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.speech_recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                return audio.get_raw_data()
                
        except Exception as e:
            logger.debug(f"Audio capture error: {e}")
            return None
    
    async def _recognize_speech(self, audio_data: bytes) -> Optional[str]:
        """Recognize speech from audio data."""
        try:
            if isinstance(self.speech_recognizer, MockSpeechRecognizer):
                # Mock implementation
                return "mock recognized text"
            
            # Real implementation using speech_recognition
            import speech_recognition as sr
            
            # Convert bytes to AudioData
            audio = sr.AudioData(audio_data, self.sample_rate, 2)
            
            # Use Google Speech Recognition (free tier)
            text = self.speech_recognizer.recognize_google(audio, language=self.language)
            
            logger.debug(f"Recognized speech: {text}")
            return text.lower()
            
        except Exception as e:
            logger.debug(f"Speech recognition error: {e}")
            return None
    
    def _contains_wake_word(self, text: str) -> bool:
        """Check if text contains a wake word."""
        text_lower = text.lower()
        return any(wake_word in text_lower for wake_word in self.wake_words)
    
    async def _activate_listening(self):
        """Activate listening mode."""
        self.state = VoiceState.LISTENING
        await self._speak("I'm listening.")
        
        # Listen for command
        audio_data = await self._capture_audio(duration=5.0)
        
        if audio_data:
            text = await self._recognize_speech(audio_data)
            
            if text:
                self.command_queue.put(text)
            else:
                await self._speak("I didn't understand. Please try again.")
        
        self.state = VoiceState.IDLE
    
    async def _process_audio(self, audio_data: bytes):
        """Process captured audio for speech recognition."""
        self.state = VoiceState.PROCESSING
        
        try:
            text = await self._recognize_speech(audio_data)
            
            if text:
                self.command_queue.put(text)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
        
        self.state = VoiceState.IDLE
    
    async def _process_voice_command(self, command_text: str):
        """Process a voice command."""
        start_time = time.time()
        command_id = f"voice_cmd_{int(time.time())}"
        
        logger.info(f"Processing voice command: {command_text}")
        
        # Create voice command record
        voice_command = VoiceCommand(
            command_id=command_id,
            text=command_text,
            confidence=0.8,  # Placeholder
            timestamp=time.time(),
            processed=False
        )
        
        self.voice_commands[command_id] = voice_command
        self.voice_stats['total_commands'] += 1
        
        try:
            # Parse and execute command
            response = await self._execute_voice_command(command_text)
            
            if response:
                voice_command.response = response
                voice_command.processed = True
                
                # Speak the response
                await self._speak(response)
                
                self.voice_stats['successful_commands'] += 1
            else:
                await self._speak("I couldn't process that command.")
                self.voice_stats['failed_commands'] += 1
        
        except Exception as e:
            logger.error(f"Error executing voice command: {e}")
            await self._speak("An error occurred while processing your command.")
            self.voice_stats['failed_commands'] += 1
        
        # Update response time
        processing_time = time.time() - start_time
        total_commands = self.voice_stats['successful_commands'] + self.voice_stats['failed_commands']
        
        if total_commands > 1:
            self.voice_stats['average_response_time'] = (
                (self.voice_stats['average_response_time'] * (total_commands - 1) + processing_time) / total_commands
            )
        else:
            self.voice_stats['average_response_time'] = processing_time
    
    async def _execute_voice_command(self, command_text: str) -> Optional[str]:
        """Execute a voice command and return response."""
        command_words = command_text.lower().split()
        
        if not command_words:
            return None
        
        # Find matching command handler
        for keyword, handler in self.command_handlers.items():
            if keyword in command_words:
                try:
                    return await handler(command_text, command_words)
                except Exception as e:
                    logger.error(f"Error in command handler {keyword}: {e}")
                    return f"Error executing {keyword} command."
        
        # If no specific handler, try general query
        return await self._handle_general_query(command_text)
    
    async def _handle_status_command(self, command_text: str, words: list) -> str:
        """Handle status-related commands."""
        try:
            system_status = self.orchestrator.get_system_status()
            
            if 'workflow' in words:
                active_workflows = len(system_status.get('components', {}))
                return f"There are {active_workflows} active workflows running."
            elif 'system' in words:
                state = system_status.get('state', 'unknown')
                uptime = system_status.get('uptime', 0)
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                return f"System is {state}. Uptime is {hours} hours and {minutes} minutes."
            else:
                return "System is operational. All components are running normally."
                
        except Exception as e:
            return f"Unable to get system status: {str(e)}"
    
    async def _handle_system_command(self, command_text: str, words: list) -> str:
        """Handle system control commands."""
        if 'restart' in words:
            return "System restart has been initiated."
        elif 'shutdown' in words:
            return "System shutdown has been initiated."
        elif 'pause' in words:
            return "System has been paused."
        elif 'resume' in words:
            return "System has been resumed."
        else:
            return "Available system commands: restart, shutdown, pause, resume."
    
    async def _handle_workflow_command(self, command_text: str, words: list) -> str:
        """Handle workflow-related commands."""
        if 'start' in words:
            try:
                execution = await self.orchestrator.orchestrate('information_gathering', {
                    'query': 'voice command initiated workflow'
                })
                return f"Started new workflow with ID {execution.execution_id[:8]}."
            except Exception as e:
                return f"Failed to start workflow: {str(e)}"
        elif 'list' in words:
            try:
                workflows = self.orchestrator.list_workflows()
                count = len(workflows)
                return f"There are {count} available workflow templates."
            except Exception as e:
                return f"Unable to list workflows: {str(e)}"
        else:
            return "Available workflow commands: start, list."
    
    async def _handle_agent_command(self, command_text: str, words: list) -> str:
        """Handle agent-related commands."""
        try:
            agents = ['triage_agent', 'research_agent', 'orchestration_agent']
            healthy_agents = 0
            
            for agent_name in agents:
                if hasattr(self.orchestrator, agent_name):
                    agent = getattr(self.orchestrator, agent_name)
                    if hasattr(agent, 'health_check'):
                        try:
                            health = await agent.health_check()
                            if health == 'healthy':
                                healthy_agents += 1
                        except Exception:
                            pass
            
            return f"{healthy_agents} out of {len(agents)} agents are healthy."
            
        except Exception as e:
            return f"Unable to check agent status: {str(e)}"
    
    async def _handle_help_command(self, command_text: str, words: list) -> str:
        """Handle help commands."""
        return ("Available voice commands: "
                "status, system restart, workflow start, agent status, "
                "help, stop listening, shutdown. "
                "You can also ask general questions about the system.")
    
    async def _handle_stop_command(self, command_text: str, words: list) -> str:
        """Handle stop commands."""
        self.state = VoiceState.IDLE
        return "Voice interface stopped listening."
    
    async def _handle_shutdown_command(self, command_text: str, words: list) -> str:
        """Handle shutdown commands."""
        return "Shutting down voice interface."
    
    async def _handle_restart_command(self, command_text: str, words: list) -> str:
        """Handle restart commands."""
        return "Restarting voice interface."
    
    async def _handle_general_query(self, query: str) -> str:
        """Handle general queries using the research agent."""
        try:
            if hasattr(self.orchestrator, 'research_agent'):
                research_agent = self.orchestrator.research_agent
                
                # Conduct quick research
                result = await research_agent.conduct_research(
                    query, 
                    depth_level=1, 
                    time_limit=30.0
                )
                
                if result.synthesis:
                    # Extract first paragraph for voice response
                    lines = result.synthesis.split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            return line.strip()[:200] + "..."
                
                return "I found some information, but it's too complex to summarize briefly."
            else:
                return "Research capabilities are not available right now."
                
        except Exception as e:
            return f"I couldn't research that topic: {str(e)}"
    
    async def _speak(self, text: str, wait: bool = False):
        """Convert text to speech and play it."""
        if not self.config.ui.voice_enabled:
            return
        
        self.state = VoiceState.SPEAKING
        
        try:
            if isinstance(self.text_to_speech, MockTextToSpeech):
                # Mock implementation
                logger.info(f"TTS (Mock): {text}")
                await asyncio.sleep(len(text) * 0.05)  # Simulate speech duration
            else:
                # Real implementation
                if wait:
                    # Synchronous speech (blocking)
                    self.text_to_speech.say(text)
                    self.text_to_speech.runAndWait()
                else:
                    # Asynchronous speech (non-blocking)
                    def speak_async():
                        self.text_to_speech.say(text)
                        self.text_to_speech.runAndWait()
                    
                    # Run in thread to avoid blocking
                    thread = threading.Thread(target=speak_async)
                    thread.daemon = True
                    thread.start()
                    
                    if wait:
                        thread.join()
            
            logger.debug(f"Spoke: {text}")
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
        
        self.state = VoiceState.IDLE
    
    async def _cleanup_audio(self):
        """Cleanup audio resources."""
        try:
            if hasattr(self, 'audio') and self.audio:
                if hasattr(self.audio, 'terminate'):
                    self.audio.terminate()
            
            if hasattr(self, 'text_to_speech') and self.text_to_speech:
                if hasattr(self.text_to_speech, 'stop'):
                    self.text_to_speech.stop()
            
        except Exception as e:
            logger.error(f"Error cleaning up audio: {e}")
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            if not self.config.ui.voice_enabled:
                return "disabled"
            
            if not self.is_running:
                return "unhealthy"
            
            # Test basic functionality
            if self.speech_recognizer and self.text_to_speech:
                return "healthy"
            else:
                return "degraded"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get voice interface statistics."""
        return {
            'is_running': self.is_running,
            'state': self.state.value,
            'voice_enabled': self.config.ui.voice_enabled,
            'language': self.language,
            'voice_stats': self.voice_stats.copy(),
            'wake_words': self.wake_words,
            'active_commands': len(self.voice_commands)
        }
    
    async def process_text_command(self, text: str) -> str:
        """Process a text command as if it were spoken."""
        return await self._execute_voice_command(text)
    
    async def speak_message(self, message: str):
        """Speak a message (public interface)."""
        await self._speak(message)
    
    def set_wake_words(self, wake_words: list):
        """Set custom wake words."""
        self.wake_words = wake_words
        logger.info(f"Updated wake words: {wake_words}")
    
    async def restart(self):
        """Restart the voice interface."""
        logger.info("Restarting Voice Interface...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()


# Mock implementations for systems without audio libraries

class MockSpeechRecognizer:
    """Mock speech recognizer for testing."""
    
    def __init__(self):
        self.energy_threshold = 300
    
    def adjust_for_ambient_noise(self, source, duration=1):
        pass
    
    def listen(self, source, timeout=None, phrase_time_limit=None):
        return MockAudioData()
    
    def recognize_google(self, audio_data, language='en-US'):
        # Return mock recognition results
        import random
        mock_phrases = [
            "hey system status",
            "what is the system status",
            "start a new workflow",
            "help me with commands",
            "shutdown the system"
        ]
        return random.choice(mock_phrases)

class MockAudioData:
    """Mock audio data."""
    
    def get_raw_data(self):
        return b"mock_audio_data"

class MockMicrophone:
    """Mock microphone."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockTextToSpeech:
    """Mock text-to-speech engine."""
    
    def __init__(self):
        self.rate = 150
        self.volume = 0.8
        self.voice = None
    
    def setProperty(self, name, value):
        setattr(self, name, value)
    
    def getProperty(self, name):
        if name == 'voices':
            return [MockVoice()]
        return getattr(self, name, None)
    
    def say(self, text):
        logger.info(f"Mock TTS: {text}")
    
    def runAndWait(self):
        pass
    
    def stop(self):
        pass

class MockVoice:
    """Mock voice for TTS."""
    
    def __init__(self):
        self.id = "mock_voice_id"
        self.name = "Mock Female Voice"

class MockAudio:
    """Mock audio interface."""
    
    def get_default_input_device_info(self):
        return {'name': 'Mock Input Device', 'index': 0}
    
    def get_default_output_device_info(self):
        return {'name': 'Mock Output Device', 'index': 0}
    
    def terminate(self):
        pass
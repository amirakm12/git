"""
Voice Pipeline for IGED
Handles speech recognition using Whisper
"""

import threading
import queue
import time
import logging
from typing import Optional, Callable

# Try to import voice recognition libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoicePipeline:
    def __init__(self, command_parser, orchestrator, memory_engine):
        self.parser = command_parser
        self.orchestrator = orchestrator
        self.memory = memory_engine
        self.recognizer = None
        self.whisper_model = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.callback_queue = queue.Queue()
        
        # Initialize voice recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        
        # Initialize Whisper model
        self.initialize_whisper()
    
    def initialize_whisper(self):
        """Initialize Whisper model for offline speech recognition"""
        try:
            logger.info("🎤 Initializing Whisper model...")
            self.whisper_model = whisper.load_model("base")
            logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            self.whisper_model = None
    
    def start_listening(self):
        """Start continuous voice listening"""
        if self.is_listening:
            logger.warning("🎤 Already listening")
            return
        
        self.is_listening = True
        logger.info("🎤 Starting voice listening...")
        
        # Start audio processing thread
        audio_thread = threading.Thread(target=self._audio_processing_loop, daemon=True)
        audio_thread.start()
        
        # Start callback processing thread
        callback_thread = threading.Thread(target=self._callback_processing_loop, daemon=True)
        callback_thread.start()
        
        # Start microphone listening
        self._listen_microphone()
    
    def stop_listening(self):
        """Stop voice listening"""
        self.is_listening = False
        logger.info("🛑 Voice listening stopped")
    
    def _listen_microphone(self):
        """Listen to microphone input"""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer:
            logger.error("❌ Speech recognition not available")
            return
            
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("🎤 Microphone ready")
                
                while self.is_listening:
                    try:
                        logger.debug("🎤 Listening for speech...")
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"❌ Microphone error: {e}")
                        time.sleep(1)
                        
        except Exception as e:
            logger.error(f"❌ Failed to initialize microphone: {e}")
    
    def _audio_processing_loop(self):
        """Process audio from queue"""
        while self.is_listening:
            try:
                audio = self.audio_queue.get(timeout=1)
                self._process_audio(audio)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Audio processing error: {e}")
    
    def _process_audio(self, audio):
        """Process audio and convert to text"""
        try:
            # Try Whisper first (offline)
            if self.whisper_model:
                text = self._whisper_transcribe(audio)
            else:
                # Fallback to speech recognition
                text = self._speech_recognition_transcribe(audio)
            
            if text and text.strip():
                logger.info(f"🎤 Transcribed: {text}")
                self._handle_transcription(text)
            else:
                logger.debug("🎤 No speech detected")
                
        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {e}")
    
    def _whisper_transcribe(self, audio) -> str:
        """Transcribe audio using Whisper"""
        try:
            if not self.whisper_model:
                return ""
                
            # Convert audio to format Whisper can process
            audio_data = audio.get_wav_data()
            
            # Save temporary audio file
            temp_file = "temp_audio.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(temp_file)
            
            # Clean up
            import os
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return result["text"].strip()
            
        except Exception as e:
            logger.error(f"❌ Whisper transcription failed: {e}")
            return ""
    
    def _speech_recognition_transcribe(self, audio) -> str:
        """Transcribe audio using speech recognition"""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer:
            return ""
            
        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            logger.error(f"❌ Speech recognition service error: {e}")
            return ""
    
    def _handle_transcription(self, text: str):
        """Handle transcribed text"""
        try:
            # Parse command
            command = self.parser.parse_command(text)
            
            # Execute command
            result = self.orchestrator.execute_command(command)
            
            # Store in memory
            self.memory.add_entry(
                command=text,
                result=str(result),
                agent=command.get('agent', 'unknown'),
                success=True
            )
            
            # Queue callback for UI update
            self.callback_queue.put({
                'type': 'voice_command',
                'text': text,
                'result': result,
                'command': command
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to handle transcription: {e}")
            self.memory.add_entry(
                command=text,
                result=f"Error: {str(e)}",
                agent='unknown',
                success=False
            )
    
    def _callback_processing_loop(self):
        """Process callbacks for UI updates"""
        while self.is_listening:
            try:
                callback = self.callback_queue.get(timeout=1)
                self._process_callback(callback)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Callback processing error: {e}")
    
    def _process_callback(self, callback):
        """Process callback for UI update"""
        try:
            # This will be handled by the GUI
            logger.debug(f"📡 Callback: {callback['type']}")
        except Exception as e:
            logger.error(f"❌ Callback processing failed: {e}")
    
    def process_text_command(self, text: str):
        """Process text command directly"""
        try:
            logger.info(f"⌨️ Processing text command: {text}")
            self._handle_transcription(text)
        except Exception as e:
            logger.error(f"❌ Failed to process text command: {e}")
    
    def get_status(self) -> dict:
        """Get voice pipeline status"""
        return {
            'is_listening': self.is_listening,
            'whisper_loaded': self.whisper_model is not None,
            'audio_queue_size': self.audio_queue.qsize(),
            'callback_queue_size': self.callback_queue.qsize()
        } 
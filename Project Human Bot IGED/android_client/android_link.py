"""
Android Client Integration for IGED
Enables remote control from Android devices
"""

import socket
import json
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import requests

logger = logging.getLogger(__name__)

class AndroidLink:
    def __init__(self, host: str = '0.0.0.0', port: int = 9090):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.running = False
        self.command_handler = None
        self.status_callback = None
        
        # Android client info
        self.android_clients = {}
        
        # Command history for Android
        self.command_history = []
        self.max_history = 100
    
    def set_command_handler(self, handler: Callable):
        """Set the command handler function"""
        self.command_handler = handler
    
    def set_status_callback(self, callback: Callable):
        """Set the status callback function"""
        self.status_callback = callback
    
    def start_server(self):
        """Start the Android link server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"📱 Android link server started on {self.host}:{self.port}")
            
            # Start client handling thread
            client_thread = threading.Thread(target=self._handle_clients, daemon=True)
            client_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Android link server: {e}")
            return False
    
    def stop_server(self):
        """Stop the Android link server"""
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("🛑 Android link server stopped")
    
    def _handle_clients(self):
        """Handle incoming Android client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"📱 Android client connected: {address}")
                
                # Add to clients list
                self.clients.append(client_socket)
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Client handling error: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle individual Android client"""
        try:
            # Send welcome message
            welcome_msg = {
                'type': 'welcome',
                'message': 'Connected to IGED Android Link',
                'version': '1.0.0',
                'timestamp': time.time()
            }
            self._send_to_client(client_socket, welcome_msg)
            
            # Register client
            client_id = f"android_{address[0]}_{int(time.time())}"
            self.android_clients[client_id] = {
                'socket': client_socket,
                'address': address,
                'connected_at': time.time(),
                'last_activity': time.time()
            }
            
            # Notify status callback
            if self.status_callback:
                self.status_callback('android_client_connected', client_id)
            
            # Handle client messages
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    # Parse message
                    message = json.loads(data.decode('utf-8'))
                    self._process_client_message(client_id, message)
                    
                    # Update last activity
                    self.android_clients[client_id]['last_activity'] = time.time()
                    
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON from client {address}")
                except Exception as e:
                    logger.error(f"❌ Client message handling error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Client handler error: {e}")
        finally:
            # Clean up client
            self._remove_client(client_id, client_socket)
    
    def _process_client_message(self, client_id: str, message: Dict[str, Any]):
        """Process message from Android client"""
        try:
            msg_type = message.get('type', 'unknown')
            
            if msg_type == 'command':
                self._handle_command(client_id, message)
            elif msg_type == 'status_request':
                self._handle_status_request(client_id)
            elif msg_type == 'ping':
                self._handle_ping(client_id)
            elif msg_type == 'voice_command':
                self._handle_voice_command(client_id, message)
            else:
                logger.warning(f"⚠️ Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
    
    def _handle_command(self, client_id: str, message: Dict[str, Any]):
        """Handle command from Android client"""
        try:
            command = message.get('command', '')
            if not command:
                return
            
            logger.info(f"📱 Android command from {client_id}: {command}")
            
            # Add to command history
            self.command_history.append({
                'client_id': client_id,
                'command': command,
                'timestamp': time.time()
            })
            
            # Trim history
            if len(self.command_history) > self.max_history:
                self.command_history = self.command_history[-self.max_history:]
            
            # Execute command if handler is set
            if self.command_handler:
                result = self.command_handler(command)
                
                # Send result back to client
                response = {
                    'type': 'command_result',
                    'command': command,
                    'result': str(result),
                    'success': True,
                    'timestamp': time.time()
                }
                
                self._send_to_client(self.android_clients[client_id]['socket'], response)
            else:
                logger.warning("⚠️ No command handler set")
                
        except Exception as e:
            logger.error(f"❌ Command handling error: {e}")
    
    def _handle_status_request(self, client_id: str):
        """Handle status request from Android client"""
        try:
            status = self._get_system_status()
            
            response = {
                'type': 'status_response',
                'status': status,
                'timestamp': time.time()
            }
            
            self._send_to_client(self.android_clients[client_id]['socket'], response)
            
        except Exception as e:
            logger.error(f"❌ Status request handling error: {e}")
    
    def _handle_ping(self, client_id: str):
        """Handle ping from Android client"""
        try:
            response = {
                'type': 'pong',
                'timestamp': time.time()
            }
            
            self._send_to_client(self.android_clients[client_id]['socket'], response)
            
        except Exception as e:
            logger.error(f"❌ Ping handling error: {e}")
    
    def _handle_voice_command(self, client_id: str, message: Dict[str, Any]):
        """Handle voice command from Android client"""
        try:
            voice_data = message.get('voice_data', '')
            if not voice_data:
                return
            
            logger.info(f"🎤 Android voice command from {client_id}")
            
            # Process voice data (base64 encoded)
            import base64
            try:
                # Save voice data to temporary file
                voice_file = f"temp_voice_{client_id}_{int(time.time())}.wav"
                with open(voice_file, 'wb') as f:
                    f.write(base64.b64decode(voice_data))
                
                # Process voice file (would integrate with voice pipeline)
                # For now, just acknowledge
                response = {
                    'type': 'voice_result',
                    'message': 'Voice command received',
                    'timestamp': time.time()
                }
                
                self._send_to_client(self.android_clients[client_id]['socket'], response)
                
                # Clean up temp file
                import os
                if os.path.exists(voice_file):
                    os.remove(voice_file)
                    
            except Exception as e:
                logger.error(f"❌ Voice data processing error: {e}")
                
        except Exception as e:
            logger.error(f"❌ Voice command handling error: {e}")
    
    def _send_to_client(self, client_socket: socket.socket, message: Dict[str, Any]):
        """Send message to Android client"""
        try:
            data = json.dumps(message).encode('utf-8')
            client_socket.send(data)
        except Exception as e:
            logger.error(f"❌ Failed to send message to client: {e}")
    
    def _remove_client(self, client_id: str, client_socket: socket.socket):
        """Remove client from tracking"""
        try:
            # Remove from clients list
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            
            # Remove from Android clients
            if client_id in self.android_clients:
                del self.android_clients[client_id]
            
            # Close socket
            client_socket.close()
            
            logger.info(f"📱 Android client disconnected: {client_id}")
            
            # Notify status callback
            if self.status_callback:
                self.status_callback('android_client_disconnected', client_id)
                
        except Exception as e:
            logger.error(f"❌ Client removal error: {e}")
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status for Android clients"""
        try:
            return {
                'server_running': self.running,
                'connected_clients': len(self.android_clients),
                'total_commands': len(self.command_history),
                'uptime': time.time() - (min([c['connected_at'] for c in self.android_clients.values()]) if self.android_clients else time.time()),
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"❌ Status generation error: {e}")
            return {}
    
    def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all Android clients"""
        try:
            for client_id, client_info in self.android_clients.items():
                try:
                    self._send_to_client(client_info['socket'], message)
                except Exception as e:
                    logger.error(f"❌ Failed to broadcast to {client_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Broadcast error: {e}")
    
    def get_connected_clients(self) -> Dict[str, Any]:
        """Get information about connected Android clients"""
        clients_info = {}
        
        for client_id, client_info in self.android_clients.items():
            clients_info[client_id] = {
                'address': client_info['address'],
                'connected_at': client_info['connected_at'],
                'last_activity': client_info['last_activity'],
                'uptime': time.time() - client_info['connected_at']
            }
        
        return clients_info
    
    def get_command_history(self, limit: int = 50) -> list:
        """Get recent command history"""
        return self.command_history[-limit:] if self.command_history else []
    
    def cleanup_inactive_clients(self, timeout: int = 300):
        """Clean up inactive clients"""
        try:
            current_time = time.time()
            inactive_clients = []
            
            for client_id, client_info in self.android_clients.items():
                if current_time - client_info['last_activity'] > timeout:
                    inactive_clients.append(client_id)
            
            for client_id in inactive_clients:
                logger.info(f"📱 Cleaning up inactive client: {client_id}")
                self._remove_client(client_id, self.android_clients[client_id]['socket'])
                
        except Exception as e:
            logger.error(f"❌ Client cleanup error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get Android link status"""
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'connected_clients': len(self.android_clients),
            'total_clients_handled': len(self.command_history),
            'server_uptime': time.time() - (min([c['connected_at'] for c in self.android_clients.values()]) if self.android_clients else time.time())
        }

# Global Android link instance
android_link = AndroidLink()

def start_android_link(host: str = '0.0.0.0', port: int = 9090):
    """Start the Android link server"""
    global android_link
    android_link = AndroidLink(host, port)
    return android_link.start_server()

def stop_android_link():
    """Stop the Android link server"""
    global android_link
    android_link.stop_server()

def set_android_command_handler(handler: Callable):
    """Set the command handler for Android clients"""
    global android_link
    android_link.set_command_handler(handler)

def set_android_status_callback(callback: Callable):
    """Set the status callback for Android events"""
    global android_link
    android_link.set_status_callback(callback) 
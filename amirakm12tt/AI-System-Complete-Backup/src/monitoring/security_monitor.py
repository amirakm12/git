"""
Security Monitor
Comprehensive security monitoring and threat detection
"""

import asyncio
import logging
import time
import hashlib
import os
import subprocess
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import deque, defaultdict
import psutil
import socket
import re

from ..core.config import SystemConfig

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(Enum):
    """Types of security events."""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_PROCESS = "suspicious_process"
    NETWORK_ANOMALY = "network_anomaly"
    FILE_INTEGRITY = "file_integrity"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALWARE_DETECTION = "malware_detection"
    BRUTE_FORCE = "brute_force"
    DATA_EXFILTRATION = "data_exfiltration"

@dataclass
class SecurityEvent:
    """Security event data."""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    title: str
    description: str
    source_ip: Optional[str]
    source_process: Optional[str]
    affected_resource: str
    timestamp: float
    evidence: Dict[str, Any]
    mitigation_actions: List[str]
    acknowledged: bool

@dataclass
class ThreatIndicator:
    """Threat indicator pattern."""
    indicator_id: str
    pattern: str
    indicator_type: str
    threat_level: ThreatLevel
    description: str
    last_seen: float

class SecurityMonitor:
    """Comprehensive security monitoring service."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_running = False
        
        # Security events
        self.security_events = deque(maxlen=10000)
        self.active_threats = {}
        self.threat_indicators = {}
        
        # Monitoring state
        self.baseline_network_connections = set()
        self.baseline_processes = set()
        self.file_integrity_hashes = {}
        self.failed_login_attempts = defaultdict(list)
        
        # Security rules and patterns
        self.threat_patterns = self._initialize_threat_patterns()
        self.suspicious_processes = self._initialize_suspicious_processes()
        self.malware_signatures = self._initialize_malware_signatures()
        
        # Performance metrics
        self.security_stats = {
            'total_events': 0,
            'critical_threats': 0,
            'blocked_attempts': 0,
            'scans_performed': 0,
            'uptime': 0.0
        }
        
        logger.info("Security Monitor initialized")
    
    def _initialize_threat_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize threat detection patterns."""
        return {
            'suspicious_network': {
                'patterns': [
                    r'.*\.onion$',  # Tor hidden services
                    r'.*\.bit$',    # Namecoin domains
                    r'.*\.i2p$',    # I2P domains
                ],
                'threat_level': ThreatLevel.MEDIUM,
                'description': 'Connection to suspicious network domains'
            },
            'suspicious_ports': {
                'ports': [1337, 31337, 4444, 5555, 6666, 8080, 9999],
                'threat_level': ThreatLevel.MEDIUM,
                'description': 'Connection to commonly used malware ports'
            },
            'privilege_escalation': {
                'patterns': [
                    r'sudo\s+su\s*-',
                    r'chmod\s+777',
                    r'chown\s+root',
                    r'setuid\s+0'
                ],
                'threat_level': ThreatLevel.HIGH,
                'description': 'Potential privilege escalation attempt'
            },
            'data_exfiltration': {
                'patterns': [
                    r'scp\s+.*@.*:',
                    r'rsync\s+.*@.*:',
                    r'curl\s+-X\s+POST.*--data',
                    r'wget\s+--post-data'
                ],
                'threat_level': ThreatLevel.HIGH,
                'description': 'Potential data exfiltration activity'
            }
        }
    
    def _initialize_suspicious_processes(self) -> Set[str]:
        """Initialize list of suspicious process names."""
        return {
            'keylogger', 'backdoor', 'trojan', 'rootkit', 'malware',
            'cryptominer', 'botnet', 'ransomware', 'spyware', 'adware',
            'netcat', 'ncat', 'socat', 'telnet', 'rsh', 'rlogin',
            'mimikatz', 'psexec', 'wce', 'gsecdump', 'pwdump'
        }
    
    def _initialize_malware_signatures(self) -> Dict[str, str]:
        """Initialize basic malware signatures."""
        return {
            'eicar_test': '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f',
            # Add more known malware hashes here
        }
    
    async def initialize(self):
        """Initialize the security monitor."""
        logger.info("Initializing Security Monitor...")
        
        try:
            # Establish security baseline
            await self._establish_security_baseline()
            
            # Initialize file integrity monitoring
            await self._initialize_file_integrity()
            
            # Load threat intelligence
            await self._load_threat_intelligence()
            
            logger.info("Security Monitor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Security Monitor: {e}")
            raise
    
    async def start(self):
        """Start the security monitor."""
        logger.info("Starting Security Monitor...")
        
        try:
            # Start security monitoring tasks
            self.monitoring_tasks = {
                'process_monitor': asyncio.create_task(self._process_monitoring_loop()),
                'network_monitor': asyncio.create_task(self._network_monitoring_loop()),
                'file_integrity': asyncio.create_task(self._file_integrity_loop()),
                'login_monitor': asyncio.create_task(self._login_monitoring_loop()),
                'malware_scanner': asyncio.create_task(self._malware_scanning_loop()),
                'threat_analyzer': asyncio.create_task(self._threat_analysis_loop()),
                'incident_response': asyncio.create_task(self._incident_response_loop()),
                'cleanup_manager': asyncio.create_task(self._cleanup_management_loop())
            }
            
            self.is_running = True
            self.start_time = time.time()
            
            logger.info("Security Monitor started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Security Monitor: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the security monitor."""
        logger.info("Shutting down Security Monitor...")
        
        self.is_running = False
        
        # Cancel monitoring tasks
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled {task_name}")
        
        # Save security data
        await self._save_security_data()
        
        logger.info("Security Monitor shutdown complete")
    
    async def _establish_security_baseline(self):
        """Establish baseline for normal system behavior."""
        logger.info("Establishing security baseline...")
        
        # Baseline network connections
        try:
            connections = psutil.net_connections()
            for conn in connections:
                if conn.laddr and conn.raddr:
                    self.baseline_network_connections.add(
                        f"{conn.laddr.ip}:{conn.laddr.port}->{conn.raddr.ip}:{conn.raddr.port}"
                    )
        except Exception as e:
            logger.warning(f"Could not establish network baseline: {e}")
        
        # Baseline processes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    self.baseline_processes.add(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.warning(f"Could not establish process baseline: {e}")
        
        logger.info(f"Security baseline established - "
                   f"Network connections: {len(self.baseline_network_connections)}, "
                   f"Processes: {len(self.baseline_processes)}")
    
    async def _initialize_file_integrity(self):
        """Initialize file integrity monitoring."""
        critical_files = [
            '/etc/passwd', '/etc/shadow', '/etc/sudoers', '/etc/hosts',
            '/boot/grub/grub.cfg', '/etc/ssh/sshd_config'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        file_hash = hashlib.sha256(content).hexdigest()
                        self.file_integrity_hashes[file_path] = {
                            'hash': file_hash,
                            'size': len(content),
                            'mtime': os.path.getmtime(file_path),
                            'checked_at': time.time()
                        }
                except Exception as e:
                    logger.warning(f"Could not hash file {file_path}: {e}")
    
    async def _load_threat_intelligence(self):
        """Load threat intelligence data."""
        # Placeholder for loading external threat intelligence
        pass
    
    async def _process_monitoring_loop(self):
        """Monitor processes for suspicious activity."""
        while self.is_running:
            try:
                current_processes = set()
                suspicious_found = []
                
                for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username']):
                    try:
                        proc_info = proc.info
                        proc_name = proc_info['name'].lower()
                        current_processes.add(proc_name)
                        
                        # Check for suspicious process names
                        if any(suspicious in proc_name for suspicious in self.suspicious_processes):
                            suspicious_found.append(proc_info)
                        
                        # Check for new processes not in baseline
                        if proc_name not in self.baseline_processes:
                            # Analyze new process
                            await self._analyze_new_process(proc_info)
                        
                        # Check command line for suspicious patterns
                        if proc_info['cmdline']:
                            cmdline = ' '.join(proc_info['cmdline'])
                            await self._analyze_command_line(proc_info, cmdline)
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Generate alerts for suspicious processes
                for proc_info in suspicious_found:
                    await self._generate_security_event(
                        SecurityEventType.SUSPICIOUS_PROCESS,
                        ThreatLevel.HIGH,
                        f"Suspicious process detected: {proc_info['name']}",
                        f"Process {proc_info['name']} (PID: {proc_info['pid']}) matches known malware patterns",
                        affected_resource=f"PID:{proc_info['pid']}",
                        evidence={'process_info': proc_info},
                        source_process=proc_info['name']
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _analyze_new_process(self, proc_info: Dict[str, Any]):
        """Analyze a new process that wasn't in baseline."""
        proc_name = proc_info['name'].lower()
        
        # Check if process executable exists in suspicious locations
        if proc_info['exe']:
            exe_path = proc_info['exe'].lower()
            suspicious_paths = ['/tmp/', '/var/tmp/', '/dev/shm/', '/home/']
            
            if any(path in exe_path for path in suspicious_paths):
                await self._generate_security_event(
                    SecurityEventType.SUSPICIOUS_PROCESS,
                    ThreatLevel.MEDIUM,
                    f"Process started from suspicious location: {proc_name}",
                    f"Process {proc_name} started from potentially unsafe location: {exe_path}",
                    affected_resource=f"PID:{proc_info['pid']}",
                    evidence={'process_info': proc_info, 'executable_path': exe_path},
                    source_process=proc_name
                )
    
    async def _analyze_command_line(self, proc_info: Dict[str, Any], cmdline: str):
        """Analyze process command line for suspicious patterns."""
        for pattern_name, pattern_info in self.threat_patterns.items():
            if 'patterns' in pattern_info:
                for pattern in pattern_info['patterns']:
                    if re.search(pattern, cmdline, re.IGNORECASE):
                        await self._generate_security_event(
                            SecurityEventType.PRIVILEGE_ESCALATION if 'escalation' in pattern_name else SecurityEventType.SUSPICIOUS_PROCESS,
                            pattern_info['threat_level'],
                            f"Suspicious command detected: {pattern_name}",
                            f"Process {proc_info['name']} executed suspicious command: {cmdline[:100]}...",
                            affected_resource=f"PID:{proc_info['pid']}",
                            evidence={'process_info': proc_info, 'command_line': cmdline, 'pattern': pattern},
                            source_process=proc_info['name']
                        )
    
    async def _network_monitoring_loop(self):
        """Monitor network activity for anomalies."""
        while self.is_running:
            try:
                current_connections = []
                
                for conn in psutil.net_connections():
                    if conn.laddr and conn.raddr:
                        connection_str = f"{conn.laddr.ip}:{conn.laddr.port}->{conn.raddr.ip}:{conn.raddr.port}"
                        current_connections.append(connection_str)
                        
                        # Check for connections to suspicious ports
                        if conn.raddr.port in self.threat_patterns['suspicious_ports']['ports']:
                            await self._generate_security_event(
                                SecurityEventType.NETWORK_ANOMALY,
                                ThreatLevel.MEDIUM,
                                f"Connection to suspicious port: {conn.raddr.port}",
                                f"Connection detected to commonly used malware port {conn.raddr.port} on {conn.raddr.ip}",
                                affected_resource=f"{conn.laddr.ip}:{conn.laddr.port}",
                                evidence={'connection': connection_str, 'port': conn.raddr.port},
                                source_ip=conn.raddr.ip
                            )
                        
                        # Check for connections to suspicious domains (would need DNS resolution)
                        await self._check_suspicious_ip(conn.raddr.ip)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in network monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_suspicious_ip(self, ip_address: str):
        """Check if IP address is suspicious."""
        # Check for private/local IPs (less suspicious)
        if ip_address.startswith(('127.', '10.', '192.168.', '172.')):
            return
        
        # Check against known bad IP ranges (placeholder)
        # In a real implementation, this would check against threat intelligence feeds
        suspicious_ranges = ['0.0.0.0/8', '127.0.0.0/8']  # Example ranges
        
        # For now, just log external connections for analysis
        logger.debug(f"External connection detected to: {ip_address}")
    
    async def _file_integrity_loop(self):
        """Monitor file integrity."""
        while self.is_running:
            try:
                for file_path, baseline in self.file_integrity_hashes.items():
                    if os.path.exists(file_path):
                        try:
                            current_mtime = os.path.getmtime(file_path)
                            
                            # Check if file was modified
                            if current_mtime > baseline['mtime']:
                                with open(file_path, 'rb') as f:
                                    content = f.read()
                                    current_hash = hashlib.sha256(content).hexdigest()
                                
                                if current_hash != baseline['hash']:
                                    await self._generate_security_event(
                                        SecurityEventType.FILE_INTEGRITY,
                                        ThreatLevel.HIGH,
                                        f"Critical file modified: {file_path}",
                                        f"System file {file_path} has been modified unexpectedly",
                                        affected_resource=file_path,
                                        evidence={
                                            'original_hash': baseline['hash'],
                                            'current_hash': current_hash,
                                            'original_mtime': baseline['mtime'],
                                            'current_mtime': current_mtime
                                        }
                                    )
                                    
                                    # Update baseline
                                    self.file_integrity_hashes[file_path] = {
                                        'hash': current_hash,
                                        'size': len(content),
                                        'mtime': current_mtime,
                                        'checked_at': time.time()
                                    }
                                    
                        except Exception as e:
                            logger.warning(f"Could not check integrity of {file_path}: {e}")
                    else:
                        # File was deleted
                        await self._generate_security_event(
                            SecurityEventType.FILE_INTEGRITY,
                            ThreatLevel.CRITICAL,
                            f"Critical file deleted: {file_path}",
                            f"System file {file_path} has been deleted",
                            affected_resource=file_path,
                            evidence={'action': 'deleted', 'original_hash': baseline['hash']}
                        )
                        
                        # Remove from monitoring
                        del self.file_integrity_hashes[file_path]
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in file integrity loop: {e}")
                await asyncio.sleep(300)
    
    async def _login_monitoring_loop(self):
        """Monitor login attempts for brute force attacks."""
        while self.is_running:
            try:
                # Monitor authentication logs (Linux)
                if os.path.exists('/var/log/auth.log'):
                    await self._check_auth_log('/var/log/auth.log')
                elif os.path.exists('/var/log/secure'):
                    await self._check_auth_log('/var/log/secure')
                
                # Check for brute force patterns
                current_time = time.time()
                for ip, attempts in list(self.failed_login_attempts.items()):
                    # Remove old attempts (older than 1 hour)
                    recent_attempts = [t for t in attempts if current_time - t < 3600]
                    self.failed_login_attempts[ip] = recent_attempts
                    
                    # Check for brute force (more than 10 attempts in 1 hour)
                    if len(recent_attempts) > 10:
                        await self._generate_security_event(
                            SecurityEventType.BRUTE_FORCE,
                            ThreatLevel.HIGH,
                            f"Brute force attack detected from {ip}",
                            f"Multiple failed login attempts ({len(recent_attempts)}) detected from {ip}",
                            affected_resource="authentication_system",
                            evidence={'failed_attempts': len(recent_attempts), 'time_window': '1 hour'},
                            source_ip=ip
                        )
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in login monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_auth_log(self, log_path: str):
        """Check authentication log for failed login attempts."""
        try:
            # Read last few lines of auth log
            result = subprocess.run(['tail', '-n', '100', log_path], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Failed password' in line or 'authentication failure' in line:
                        # Extract IP address
                        ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip_address = ip_match.group(1)
                            self.failed_login_attempts[ip_address].append(time.time())
                            
        except Exception as e:
            logger.warning(f"Could not check auth log {log_path}: {e}")
    
    async def _malware_scanning_loop(self):
        """Perform periodic malware scanning."""
        while self.is_running:
            try:
                # Simple hash-based malware detection
                await self._scan_running_processes()
                
                self.security_stats['scans_performed'] += 1
                
                await asyncio.sleep(1800)  # Scan every 30 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in malware scanning loop: {e}")
                await asyncio.sleep(1800)
    
    async def _scan_running_processes(self):
        """Scan running processes for malware signatures."""
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['exe'] and os.path.exists(proc.info['exe']):
                    # Calculate file hash
                    with open(proc.info['exe'], 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Check against known malware signatures
                    for malware_name, malware_hash in self.malware_signatures.items():
                        if file_hash == malware_hash:
                            await self._generate_security_event(
                                SecurityEventType.MALWARE_DETECTION,
                                ThreatLevel.CRITICAL,
                                f"Malware detected: {malware_name}",
                                f"Known malware {malware_name} detected in process {proc.info['name']}",
                                affected_resource=f"PID:{proc.info['pid']}",
                                evidence={
                                    'process_info': proc.info,
                                    'file_hash': file_hash,
                                    'malware_signature': malware_name
                                },
                                source_process=proc.info['name']
                            )
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError):
                pass
            except Exception as e:
                logger.warning(f"Error scanning process {proc.info.get('name', 'unknown')}: {e}")
    
    async def _threat_analysis_loop(self):
        """Analyze collected security events for patterns."""
        while self.is_running:
            try:
                # Correlate events and identify attack patterns
                await self._correlate_security_events()
                
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in threat analysis loop: {e}")
                await asyncio.sleep(300)
    
    async def _correlate_security_events(self):
        """Correlate security events to identify attack patterns."""
        # Simple correlation - look for multiple events from same source
        recent_events = [e for e in self.security_events if time.time() - e.timestamp < 3600]
        
        # Group by source IP
        events_by_ip = defaultdict(list)
        for event in recent_events:
            if event.source_ip:
                events_by_ip[event.source_ip].append(event)
        
        # Look for coordinated attacks
        for ip, events in events_by_ip.items():
            if len(events) > 3:  # Multiple events from same IP
                event_types = set(e.event_type for e in events)
                if len(event_types) > 1:  # Different types of attacks
                    await self._generate_security_event(
                        SecurityEventType.NETWORK_ANOMALY,
                        ThreatLevel.CRITICAL,
                        f"Coordinated attack detected from {ip}",
                        f"Multiple attack vectors detected from {ip}: {', '.join(et.value for et in event_types)}",
                        affected_resource="system",
                        evidence={'event_count': len(events), 'attack_types': list(event_types)},
                        source_ip=ip
                    )
    
    async def _incident_response_loop(self):
        """Handle automated incident response."""
        while self.is_running:
            try:
                # Check for critical threats requiring immediate response
                for threat_id, threat in list(self.active_threats.items()):
                    if threat.threat_level == ThreatLevel.CRITICAL and not threat.acknowledged:
                        await self._handle_critical_threat(threat)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in incident response loop: {e}")
                await asyncio.sleep(30)
    
    async def _handle_critical_threat(self, threat: SecurityEvent):
        """Handle critical security threats automatically."""
        logger.critical(f"Handling critical threat: {threat.title}")
        
        # Implement automated responses based on threat type
        if threat.event_type == SecurityEventType.MALWARE_DETECTION:
            # Could terminate malicious process
            logger.critical(f"CRITICAL: Malware detected - {threat.description}")
            
        elif threat.event_type == SecurityEventType.BRUTE_FORCE:
            # Could block IP address
            logger.critical(f"CRITICAL: Brute force attack - {threat.description}")
            self.security_stats['blocked_attempts'] += 1
            
        elif threat.event_type == SecurityEventType.FILE_INTEGRITY:
            # Could backup and restore file
            logger.critical(f"CRITICAL: File integrity violation - {threat.description}")
        
        # Mark as acknowledged to prevent repeated responses
        threat.acknowledged = True
    
    async def _cleanup_management_loop(self):
        """Manage cleanup of old security data."""
        while self.is_running:
            try:
                current_time = time.time()
                max_age = 86400 * 7  # 7 days
                
                # Clean up old security events
                old_events = [e for e in self.security_events if current_time - e.timestamp > max_age]
                for event in old_events:
                    self.security_events.remove(event)
                
                # Clean up old threat indicators
                old_indicators = [
                    tid for tid, indicator in self.threat_indicators.items()
                    if current_time - indicator.last_seen > max_age
                ]
                for tid in old_indicators:
                    del self.threat_indicators[tid]
                
                if old_events or old_indicators:
                    logger.info(f"Cleaned up {len(old_events)} old security events and "
                              f"{len(old_indicators)} old threat indicators")
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup management: {e}")
                await asyncio.sleep(3600)
    
    async def _generate_security_event(self, event_type: SecurityEventType, threat_level: ThreatLevel,
                                     title: str, description: str, affected_resource: str,
                                     evidence: Dict[str, Any], source_ip: str = None,
                                     source_process: str = None):
        """Generate a security event."""
        event_id = f"sec_{int(time.time())}_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        
        # Generate mitigation actions based on event type
        mitigation_actions = self._generate_mitigation_actions(event_type, evidence)
        
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            threat_level=threat_level,
            title=title,
            description=description,
            source_ip=source_ip,
            source_process=source_process,
            affected_resource=affected_resource,
            timestamp=time.time(),
            evidence=evidence,
            mitigation_actions=mitigation_actions,
            acknowledged=False
        )
        
        self.security_events.append(event)
        self.active_threats[event_id] = event
        self.security_stats['total_events'] += 1
        
        if threat_level == ThreatLevel.CRITICAL:
            self.security_stats['critical_threats'] += 1
        
        logger.warning(f"Security event generated: [{threat_level.value.upper()}] {title}")
    
    def _generate_mitigation_actions(self, event_type: SecurityEventType, 
                                   evidence: Dict[str, Any]) -> List[str]:
        """Generate recommended mitigation actions for security events."""
        actions = []
        
        if event_type == SecurityEventType.SUSPICIOUS_PROCESS:
            actions.extend([
                "Investigate process legitimacy",
                "Consider terminating suspicious process",
                "Scan system for malware",
                "Review process execution history"
            ])
        elif event_type == SecurityEventType.NETWORK_ANOMALY:
            actions.extend([
                "Block suspicious IP address",
                "Monitor network traffic",
                "Check firewall rules",
                "Investigate connection purpose"
            ])
        elif event_type == SecurityEventType.FILE_INTEGRITY:
            actions.extend([
                "Restore file from backup",
                "Investigate who modified the file",
                "Check system for compromise",
                "Review file access logs"
            ])
        elif event_type == SecurityEventType.BRUTE_FORCE:
            actions.extend([
                "Block attacking IP address",
                "Strengthen authentication",
                "Enable account lockout",
                "Monitor for continued attempts"
            ])
        elif event_type == SecurityEventType.MALWARE_DETECTION:
            actions.extend([
                "Quarantine infected file",
                "Terminate malicious process",
                "Full system scan",
                "Isolate affected system"
            ])
        
        return actions
    
    async def _save_security_data(self):
        """Save security data to persistent storage."""
        # Placeholder for saving security data
        pass
    
    # Public API methods
    
    async def health_check(self) -> str:
        """Perform health check."""
        try:
            if not self.is_running:
                return "unhealthy"
            
            # Check if monitoring tasks are running
            active_tasks = sum(1 for task in self.monitoring_tasks.values() if not task.done())
            
            if active_tasks >= len(self.monitoring_tasks) * 0.8:
                return "healthy"
            elif active_tasks >= len(self.monitoring_tasks) * 0.5:
                return "degraded"
            else:
                return "unhealthy"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unhealthy"
    
    async def handle_alert(self, alert_data: Dict[str, Any]):
        """Handle security alert from external source."""
        await self._generate_security_event(
            SecurityEventType.NETWORK_ANOMALY,  # Default type
            ThreatLevel.MEDIUM,
            alert_data.get('title', 'External Security Alert'),
            alert_data.get('description', 'Security alert from external source'),
            alert_data.get('resource', 'unknown'),
            alert_data
        )
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status."""
        current_time = time.time()
        
        # Recent events (last 24 hours)
        recent_events = [
            {
                'id': event.event_id,
                'type': event.event_type.value,
                'level': event.threat_level.value,
                'title': event.title,
                'timestamp': event.timestamp,
                'acknowledged': event.acknowledged
            }
            for event in self.security_events
            if current_time - event.timestamp <= 86400
        ]
        
        # Active threats
        active_threats = [
            {
                'id': threat.event_id,
                'type': threat.event_type.value,
                'level': threat.threat_level.value,
                'title': threat.title,
                'description': threat.description,
                'timestamp': threat.timestamp,
                'mitigation_actions': threat.mitigation_actions
            }
            for threat in self.active_threats.values()
            if not threat.acknowledged
        ]
        
        return {
            'security_stats': self.security_stats.copy(),
            'recent_events': recent_events,
            'active_threats': active_threats,
            'monitoring_status': {
                'is_running': self.is_running,
                'uptime': current_time - self.start_time if hasattr(self, 'start_time') else 0,
                'active_tasks': sum(1 for task in self.monitoring_tasks.values() if not task.done()) if hasattr(self, 'monitoring_tasks') else 0
            },
            'threat_indicators': len(self.threat_indicators),
            'baseline_established': {
                'network_connections': len(self.baseline_network_connections),
                'processes': len(self.baseline_processes),
                'file_integrity': len(self.file_integrity_hashes)
            }
        }
    
    def acknowledge_threat(self, event_id: str) -> bool:
        """Acknowledge a security threat."""
        if event_id in self.active_threats:
            self.active_threats[event_id].acknowledged = True
            logger.info(f"Security threat {event_id} acknowledged")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get security monitor statistics."""
        return {
            'security_stats': self.security_stats.copy(),
            'active_threats': len([t for t in self.active_threats.values() if not t.acknowledged]),
            'total_events': len(self.security_events),
            'threat_indicators': len(self.threat_indicators),
            'is_running': self.is_running
        }
    
    async def restart(self):
        """Restart the security monitor."""
        logger.info("Restarting Security Monitor...")
        await self.shutdown()
        await asyncio.sleep(1)
        await self.initialize()
        await self.start()
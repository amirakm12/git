"""
Command Parser for IGED
Converts natural language to structured commands
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class CommandParser:
    def __init__(self):
        self.command_patterns = {
            'codegen': [
                r'(?:generate|create|make|build)\s+(?:a\s+)?(?:flask|web|python|script|api|rest|html|website)',
                r'(?:write|code)\s+(?:a\s+)?(?:flask|web|python|script|api|rest|html|website)',
                r'(?:develop|program)\s+(?:a\s+)?(?:flask|web|python|script|api|rest|html|website)'
            ],
            'secops': [
                r'(?:scan|check|test|audit)\s+(?:for\s+)?(?:vulnerabilities|security|ports|network)',
                r'(?:security|penetration|vulnerability)\s+(?:scan|test|audit)',
                r'(?:port|network)\s+(?:scan|check|test)',
                r'(?:web|http|https)\s+(?:security|vulnerability)\s+(?:scan|check)'
            ],
            'advanced_secops': [
                r'(?:penetrate|hack|exploit|breach)\s+(?:into|to|the)\s+',
                r'(?:advanced|deep|comprehensive)\s+(?:penetration|security|hacking)',
                r'(?:zero.?day|exploit|vulnerability)\s+(?:scan|test|attack)',
                r'(?:persistent|backdoor|covert)\s+(?:access|connection|control)'
            ],
            'network_intelligence': [
                r'(?:monitor|surveillance|intercept)\s+(?:network|traffic|communication)',
                r'(?:capture|analyze|decode)\s+(?:packets|traffic|protocols)',
                r'(?:device|inventory|discovery)\s+(?:network|devices|systems)',
                r'(?:intelligence|reconnaissance|gathering)\s+(?:network|system)'
            ],
            'remote_control': [
                r'(?:connect|establish|control)\s+(?:remote|to|connection)',
                r'(?:execute|run|command)\s+(?:remote|on|system)',
                r'(?:deploy|payload|backdoor)\s+(?:to|on|system)',
                r'(?:monitor|surveillance)\s+(?:remote|system|device)'
            ],
            'dataminer': [
                r'(?:analyze|process|mine|extract)\s+(?:data|dataset|file)',
                r'(?:data|statistical)\s+(?:analysis|processing|mining)',
                r'(?:visualize|plot|chart)\s+(?:data|dataset)',
                r'(?:generate|create)\s+(?:statistics|stats|report)\s+(?:for|from)'
            ]
        }
        
        self.parameter_patterns = {
            'file_path': r'["\']([^"\']*\.(?:csv|xlsx|xls|json|txt|py|html|js|css))["\']',
            'url': r'https?://[^\s]+',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'hostname': r'(?:scan|check|test)\s+(?:the\s+)?([a-zA-Z0-9.-]+)',
            'target': r'(?:for|on|at)\s+([a-zA-Z0-9._-]+)'
        }
    
    def parse_command(self, text: str) -> Dict[str, Any]:
        """Parse natural language command into structured format"""
        try:
            text = text.strip()
            if not text:
                return self._create_error_command("Empty command")
            
            logger.info(f"🔍 Parsing command: {text}")
            
            # Determine command type and agent
            command_type, agent = self._identify_command_type(text)
            
            # Extract target and parameters
            target = self._extract_target(text, command_type)
            parameters = self._extract_parameters(text)
            
            # Create command structure
            command = {
                'original_text': text,
                'command_type': command_type,
                'agent': agent,
                'target': target,
                'parameters': parameters,
                'confidence': self._calculate_confidence(text, command_type),
                'timestamp': self._get_timestamp()
            }
            
            logger.info(f"✅ Parsed command: {command_type} -> {agent}")
            return command
            
        except Exception as e:
            logger.error(f"❌ Command parsing failed: {e}")
            return self._create_error_command(f"Parsing error: {str(e)}")
    
    def _identify_command_type(self, text: str) -> tuple:
        """Identify the type of command and appropriate agent"""
        text_lower = text.lower()
        
        # Check each agent's patterns
        for agent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    command_type = self._get_command_type(text_lower, agent)
                    return command_type, agent
        
        # Default to general command
        return 'general', 'orchestrator'
    
    def _get_command_type(self, text: str, agent: str) -> str:
        """Get specific command type based on agent and text"""
        if agent == 'codegen':
            if 'flask' in text or 'web' in text:
                return 'generate_web_app'
            elif 'python' in text or 'script' in text:
                return 'generate_script'
            elif 'api' in text or 'rest' in text:
                return 'generate_api'
            elif 'html' in text or 'website' in text:
                return 'generate_website'
            else:
                return 'generate_code'
        
        elif agent == 'secops':
            if 'port' in text:
                return 'port_scan'
            elif 'network' in text:
                return 'network_scan'
            elif 'web' in text or 'http' in text:
                return 'web_security_scan'
            else:
                return 'security_scan'
        
        elif agent == 'advanced_secops':
            if 'penetrate' in text or 'hack' in text:
                return 'penetration_test'
            elif 'exploit' in text:
                return 'exploit_target'
            elif 'persistent' in text or 'backdoor' in text:
                return 'establish_persistence'
            else:
                return 'advanced_security_scan'
        
        elif agent == 'network_intelligence':
            if 'monitor' in text or 'surveillance' in text:
                return 'network_monitoring'
            elif 'intercept' in text or 'capture' in text:
                return 'packet_interception'
            elif 'analyze' in text or 'intelligence' in text:
                return 'traffic_analysis'
            elif 'device' in text or 'inventory' in text:
                return 'device_discovery'
            else:
                return 'comprehensive_intelligence'
        
        elif agent == 'remote_control':
            if 'connect' in text or 'establish' in text:
                return 'establish_connection'
            elif 'control' in text or 'command' in text:
                return 'execute_remote_command'
            elif 'monitor' in text or 'surveillance' in text:
                return 'remote_monitoring'
            elif 'payload' in text or 'deploy' in text:
                return 'deploy_payload'
            else:
                return 'remote_system_control'
        
        elif agent == 'dataminer':
            if 'analyze' in text:
                return 'analyze_data'
            elif 'extract' in text or 'mine' in text:
                return 'extract_data'
            elif 'visualize' in text or 'plot' in text:
                return 'visualize_data'
            elif 'statistics' in text or 'stats' in text:
                return 'generate_statistics'
            else:
                return 'process_data'
        
        return 'execute'
    
    def _extract_target(self, text: str, command_type: str) -> str:
        """Extract target from command text"""
        # Look for file paths
        file_match = re.search(self.parameter_patterns['file_path'], text)
        if file_match:
            return file_match.group(1)
        
        # Look for URLs
        url_match = re.search(self.parameter_patterns['url'], text)
        if url_match:
            return url_match.group(0)
        
        # Look for IP addresses
        ip_match = re.search(self.parameter_patterns['ip_address'], text)
        if ip_match:
            return ip_match.group(0)
        
        # Look for hostnames
        hostname_match = re.search(self.parameter_patterns['hostname'], text, re.IGNORECASE)
        if hostname_match:
            return hostname_match.group(1)
        
        # Look for generic targets
        target_match = re.search(self.parameter_patterns['target'], text, re.IGNORECASE)
        if target_match:
            return target_match.group(1)
        
        # Extract meaningful words as target
        words = text.split()
        if len(words) > 2:
            # Skip common command words
            skip_words = {'generate', 'create', 'make', 'build', 'scan', 'check', 'test', 'analyze', 'process'}
            target_words = [word for word in words[2:] if word.lower() not in skip_words]
            if target_words:
                return ' '.join(target_words[:3])  # Limit to 3 words
        
        return text
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract parameters from command text"""
        parameters = {}
        
        # Extract file paths
        file_matches = re.findall(self.parameter_patterns['file_path'], text)
        if file_matches:
            parameters['files'] = file_matches
        
        # Extract URLs
        url_matches = re.findall(self.parameter_patterns['url'], text)
        if url_matches:
            parameters['urls'] = url_matches
        
        # Extract IP addresses
        ip_matches = re.findall(self.parameter_patterns['ip_address'], text)
        if ip_matches:
            parameters['ip_addresses'] = ip_matches
        
        # Extract boolean flags
        boolean_flags = {
            'verbose': r'\b(?:verbose|detailed|full)\b',
            'quiet': r'\b(?:quiet|silent|minimal)\b',
            'force': r'\b(?:force|overwrite)\b',
            'recursive': r'\b(?:recursive|recursively)\b'
        }
        
        for flag, pattern in boolean_flags.items():
            if re.search(pattern, text, re.IGNORECASE):
                parameters[flag] = True
        
        # Extract numeric values
        numeric_patterns = {
            'timeout': r'(?:timeout|time)\s+(\d+)',
            'limit': r'(?:limit|max|maximum)\s+(\d+)',
            'port': r'(?:port)\s+(\d+)'
        }
        
        for param, pattern in numeric_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parameters[param] = int(match.group(1))
        
        return parameters
    
    def _calculate_confidence(self, text: str, command_type: str) -> float:
        """Calculate confidence score for command parsing"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for longer, more specific commands
        if len(text.split()) > 3:
            confidence += 0.2
        
        # Increase confidence for specific keywords
        specific_keywords = ['generate', 'create', 'scan', 'analyze', 'process']
        if any(keyword in text.lower() for keyword in specific_keywords):
            confidence += 0.2
        
        # Increase confidence for file paths or URLs
        if re.search(self.parameter_patterns['file_path'], text) or re.search(self.parameter_patterns['url'], text):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _create_error_command(self, error_message: str) -> Dict[str, Any]:
        """Create error command structure"""
        return {
            'original_text': '',
            'command_type': 'error',
            'agent': 'unknown',
            'target': '',
            'parameters': {},
            'error': error_message,
            'confidence': 0.0,
            'timestamp': self._get_timestamp()
        }
    
    def get_supported_commands(self) -> Dict[str, List[str]]:
        """Get list of supported commands by agent"""
        return {
            'codegen': [
                'generate_web_app',
                'generate_script', 
                'generate_api',
                'generate_website',
                'generate_code'
            ],
            'secops': [
                'security_scan',
                'port_scan',
                'network_scan',
                'web_security_scan'
            ],
            'advanced_secops': [
                'penetration_test',
                'exploit_target',
                'establish_persistence',
                'advanced_security_scan',
                'zero_day_scanning'
            ],
            'network_intelligence': [
                'network_monitoring',
                'packet_interception',
                'traffic_analysis',
                'device_discovery',
                'comprehensive_intelligence'
            ],
            'remote_control': [
                'establish_connection',
                'execute_remote_command',
                'remote_monitoring',
                'deploy_payload',
                'remote_system_control'
            ],
            'dataminer': [
                'analyze_data',
                'extract_data',
                'visualize_data',
                'generate_statistics',
                'process_data'
            ]
        }
    
    def validate_command(self, command: Dict[str, Any]) -> bool:
        """Validate parsed command structure"""
        required_fields = ['command_type', 'agent', 'target']
        
        for field in required_fields:
            if field not in command:
                return False
        
        if command['command_type'] == 'error':
            return False
        
        return True 
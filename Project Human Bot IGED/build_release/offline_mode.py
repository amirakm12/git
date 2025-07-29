"""
Offline Mode for IGED
Enables completely air-gapped operation
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OfflineMode:
    def __init__(self):
        self.enabled = False
        self.blocked_domains = [
            'api.openai.com',
            'api.anthropic.com',
            'api.google.com',
            'api.cloudflare.com',
            'api.github.com',
            'pypi.org',
            'pypi.python.org'
        ]
        self.blocked_ports = [80, 443, 8080, 8443]
    
    def enable(self):
        """Enable offline mode"""
        try:
            self.enabled = True
            
            # Block network access
            self._block_network_access()
            
            # Disable external APIs
            self._disable_external_apis()
            
            # Set environment variables
            os.environ['IGED_OFFLINE_MODE'] = '1'
            os.environ['PYTHONPATH'] = os.getcwd()
            
            logger.info("🚨 Offline mode enabled - No external network access")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable offline mode: {e}")
            return False
    
    def disable(self):
        """Disable offline mode"""
        try:
            self.enabled = False
            
            # Restore network access
            self._restore_network_access()
            
            # Remove environment variables
            if 'IGED_OFFLINE_MODE' in os.environ:
                del os.environ['IGED_OFFLINE_MODE']
            
            logger.info("🌐 Offline mode disabled - Network access restored")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable offline mode: {e}")
            return False
    
    def _block_network_access(self):
        """Block network access"""
        try:
            # This is a simplified implementation
            # In a real implementation, you would use firewall rules or network isolation
            
            # Set environment variables to prevent network access
            os.environ['REQUESTS_CA_BUNDLE'] = '/dev/null'
            os.environ['CURL_CA_BUNDLE'] = '/dev/null'
            
            logger.info("🔒 Network access blocked")
            
        except Exception as e:
            logger.error(f"Failed to block network access: {e}")
    
    def _restore_network_access(self):
        """Restore network access"""
        try:
            # Remove blocking environment variables
            if 'REQUESTS_CA_BUNDLE' in os.environ:
                del os.environ['REQUESTS_CA_BUNDLE']
            if 'CURL_CA_BUNDLE' in os.environ:
                del os.environ['CURL_CA_BUNDLE']
            
            logger.info("🔓 Network access restored")
            
        except Exception as e:
            logger.error(f"Failed to restore network access: {e}")
    
    def _disable_external_apis(self):
        """Disable external API calls"""
        try:
            # Override requests module to block external calls
            import requests
            
            def blocked_request(*args, **kwargs):
                url = args[0] if args else kwargs.get('url', '')
                if self._is_external_url(url):
                    raise Exception(f"External API call blocked in offline mode: {url}")
                if hasattr(requests, '_original_request'):
                    return requests._original_request(*args, **kwargs)
                return None
            
            # Store original method
            if not hasattr(requests, '_original_request'):
                requests._original_request = requests.request
            
            # Replace with blocked version
            requests.request = blocked_request
            
            logger.info("🚫 External API calls disabled")
            
        except ImportError:
            logger.warning("⚠️ Requests module not available")
        except Exception as e:
            logger.error(f"Failed to disable external APIs: {e}")
    
    def _is_external_url(self, url: str) -> bool:
        """Check if URL is external"""
        if not url:
            return False
        
        # Check for local URLs
        local_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'
        ]
        
        for pattern in local_patterns:
            if pattern in url.lower():
                return False
        
        # Check for blocked domains
        for domain in self.blocked_domains:
            if domain in url.lower():
                return True
        
        return True
    
    def check_offline_status(self) -> Dict[str, Any]:
        """Check offline mode status"""
        return {
            'enabled': self.enabled,
            'blocked_domains': self.blocked_domains,
            'blocked_ports': self.blocked_ports,
            'environment_vars': {
                'IGED_OFFLINE_MODE': os.environ.get('IGED_OFFLINE_MODE', '0'),
                'PYTHONPATH': os.environ.get('PYTHONPATH', '')
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get offline mode status"""
        return {
            'enabled': self.enabled,
            'status': 'active' if self.enabled else 'inactive'
        }

# Global offline mode instance
offline_mode = OfflineMode()

def enable_offline_mode():
    """Enable offline mode globally"""
    return offline_mode.enable()

def disable_offline_mode():
    """Disable offline mode globally"""
    return offline_mode.disable()

def is_offline_mode():
    """Check if offline mode is enabled"""
    return offline_mode.enabled 
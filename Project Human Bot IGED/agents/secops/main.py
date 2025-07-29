"""
SecOps Agent for IGED
Security operations and penetration testing
"""

import subprocess
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class SecOpsAgent:
    def __init__(self, memory_engine):
        self.memory = memory_engine
        self.output_dir = Path("output/security")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, target: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Execute security operation"""
        try:
            logger.info(f"🔒 SecOps executing: {target}")
            
            if "scan" in target.lower() or "vulnerability" in target.lower():
                return self._security_scan(target)
            elif "port" in target.lower():
                return self._port_scan(target)
            elif "network" in target.lower():
                return self._network_scan(target)
            elif "web" in target.lower() or "http" in target.lower():
                return self._web_security_scan(target)
            else:
                return self._general_security_check(target)
                
        except Exception as e:
            logger.error(f"❌ SecOps execution failed: {e}")
            return f"❌ Security operation error: {str(e)}"
    
    def _security_scan(self, target: str) -> str:
        """Perform security vulnerability scan"""
        try:
            # Extract target from command
            scan_target = self._extract_target(target)
            if not scan_target:
                scan_target = "localhost"
            
            results = []
            results.append(f"🔍 Security scan initiated for: {scan_target}")
            
            # Basic port scan
            open_ports = self._scan_ports(scan_target)
            results.append(f"📡 Open ports: {open_ports}")
            
            # Service detection
            services = self._detect_services(scan_target, open_ports)
            results.append(f"🔧 Services detected: {services}")
            
            # Common vulnerability checks
            vulns = self._check_common_vulnerabilities(scan_target)
            results.append(f"⚠️ Potential vulnerabilities: {vulns}")
            
            # Save results
            report_file = self.output_dir / f"security_scan_{scan_target.replace('.', '_')}.txt"
            with open(report_file, "w") as f:
                f.write("\n".join(results))
            
            return f"✅ Security scan complete. Results saved to {report_file}\n\n" + "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Security scan failed: {e}")
            return f"❌ Security scan error: {str(e)}"
    
    def _port_scan(self, target: str) -> str:
        """Perform port scan"""
        try:
            scan_target = self._extract_target(target)
            if not scan_target:
                scan_target = "localhost"
            
            open_ports = self._scan_ports(scan_target)
            
            results = [f"🔍 Port scan for {scan_target}:"]
            for port in open_ports:
                service = self._get_service_name(port)
                results.append(f"  Port {port}: {service}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Port scan failed: {e}")
            return f"❌ Port scan error: {str(e)}"
    
    def _network_scan(self, target: str) -> str:
        """Perform network scan"""
        try:
            scan_target = self._extract_target(target)
            if not scan_target:
                scan_target = "192.168.1.0/24"  # Default local network
            
            results = [f"🌐 Network scan for {scan_target}:"]
            
            # Use nmap for network discovery
            try:
                nm = nmap.PortScanner()
                nm.scan(hosts=scan_target, arguments='-sn')
                
                for host in nm.all_hosts():
                    if nm[host].state() == 'up':
                        results.append(f"  Host: {host} - Status: UP")
                        
                        # Try to get hostname
                        try:
                            hostname = socket.gethostbyaddr(host)[0]
                            results.append(f"    Hostname: {hostname}")
                        except:
                            pass
                            
            except Exception as e:
                results.append(f"  Network scan error: {e}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Network scan failed: {e}")
            return f"❌ Network scan error: {str(e)}"
    
    def _web_security_scan(self, target: str) -> str:
        """Perform web security scan"""
        try:
            url = self._extract_url(target)
            if not url:
                url = "http://localhost"
            
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            results = [f"🌐 Web security scan for {url}:"]
            
            # Check if site is accessible
            try:
                response = requests.get(url, timeout=10)
                results.append(f"  Status: {response.status_code}")
                results.append(f"  Server: {response.headers.get('Server', 'Unknown')}")
                
                # Check for security headers
                security_headers = [
                    'X-Frame-Options',
                    'X-Content-Type-Options',
                    'X-XSS-Protection',
                    'Strict-Transport-Security',
                    'Content-Security-Policy'
                ]
                
                missing_headers = []
                for header in security_headers:
                    if header not in response.headers:
                        missing_headers.append(header)
                
                if missing_headers:
                    results.append(f"  ⚠️ Missing security headers: {missing_headers}")
                else:
                    results.append("  ✅ All security headers present")
                    
            except requests.exceptions.RequestException as e:
                results.append(f"  ❌ Cannot access {url}: {e}")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ Web security scan failed: {e}")
            return f"❌ Web security scan error: {str(e)}"
    
    def _general_security_check(self, target: str) -> str:
        """Perform general security check"""
        try:
            results = [f"🔒 General security check for: {target}"]
            
            # System information
            import platform
            results.append(f"  OS: {platform.system()} {platform.release()}")
            
            # Check for common security tools
            security_tools = ['nmap', 'wireshark', 'metasploit', 'burpsuite']
            available_tools = []
            
            for tool in security_tools:
                try:
                    subprocess.run([tool, '--version'], capture_output=True, timeout=5)
                    available_tools.append(tool)
                except:
                    pass
            
            results.append(f"  Available security tools: {available_tools}")
            
            # Network interfaces
            try:
                import psutil
                interfaces = psutil.net_if_addrs()
                results.append(f"  Network interfaces: {list(interfaces.keys())}")
            except:
                results.append("  Network interfaces: Unable to detect")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"❌ General security check failed: {e}")
            return f"❌ General security check error: {str(e)}"
    
    def _scan_ports(self, target: str) -> List[int]:
        """Scan for open ports"""
        open_ports = []
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080]
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        return open_ports
    
    def _detect_services(self, target: str, ports: List[int]) -> Dict[int, str]:
        """Detect services running on ports"""
        services = {}
        for port in ports:
            services[port] = self._get_service_name(port)
        return services
    
    def _get_service_name(self, port: int) -> str:
        """Get service name for port"""
        service_map = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            3306: "MySQL",
            5432: "PostgreSQL",
            8080: "HTTP-Alt"
        }
        return service_map.get(port, "Unknown")
    
    def _check_common_vulnerabilities(self, target: str) -> List[str]:
        """Check for common vulnerabilities"""
        vulnerabilities = []
        
        # Check for default credentials
        vulnerabilities.append("Default credentials (manual check required)")
        
        # Check for open telnet
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target, 23))
            if result == 0:
                vulnerabilities.append("Telnet service open (insecure)")
            sock.close()
        except:
            pass
        
        # Check for HTTP instead of HTTPS
        try:
            response = requests.get(f"http://{target}", timeout=5)
            if response.status_code == 200:
                vulnerabilities.append("HTTP service accessible (consider HTTPS)")
        except:
            pass
        
        return vulnerabilities
    
    def _extract_target(self, text: str) -> str:
        """Extract target from command text"""
        import re
        
        # Look for IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, text)
        if ips:
            return ips[0]
        
        # Look for hostnames
        hostname_pattern = r'(?:scan|check|test)\s+(?:the\s+)?([a-zA-Z0-9.-]+)'
        match = re.search(hostname_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return ""
    
    def _extract_url(self, text: str) -> str:
        """Extract URL from command text"""
        import re
        
        # Look for URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if urls:
            return urls[0]
        
        # Look for domain names
        domain_pattern = r'(?:scan|check|test)\s+(?:the\s+)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(domain_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'status': 'active',
            'agent': 'secops',
            'output_directory': str(self.output_dir),
            'capabilities': ['port_scan', 'vulnerability_scan', 'network_scan', 'web_security']
        } 
"""
SSL Certificate Checker
Monitors SSL/TLS certificate expiration dates
"""

import ssl
import socket
from datetime import datetime, timedelta
from urllib.parse import urlparse


class SSLChecker:
    """
    Check SSL certificate validity and expiration
    
    Alerts when certificates are about to expire
    """
    
    def __init__(self, warning_days=30, critical_days=7):
        """
        Args:
            warning_days (int): Days before expiration to warn
            critical_days (int): Days before expiration for critical alert
        """
        self.warning_days = warning_days
        self.critical_days = critical_days
    
    def check(self, host, port=443):
        """
        Check SSL certificate for a host
        
        Args:
            host (str): Hostname or URL
            port (int): HTTPS port (default 443)
        
        Returns:
            dict: Check result with certificate details
        """
        # Parse URL if full URL provided
        if host.startswith('http'):
            parsed = urlparse(host)
            host = parsed.hostname
            port = parsed.port or 443
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
            
            # Parse certificate details
            not_after = cert['notAfter']
            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            
            # Calculate days until expiration
            now = datetime.now()
            days_remaining = (expiry_date - now).days
            
            # Determine status
            if days_remaining < 0:
                status = 'expired'
                severity = 'critical'
                message = f"Certificate EXPIRED {abs(days_remaining)} days ago"
            elif days_remaining <= self.critical_days:
                status = 'expiring_soon'
                severity = 'critical'
                message = f"Certificate expires in {days_remaining} days (CRITICAL)"
            elif days_remaining <= self.warning_days:
                status = 'warning'
                severity = 'warning'
                message = f"Certificate expires in {days_remaining} days"
            else:
                status = 'valid'
                severity = 'ok'
                message = f"Certificate valid for {days_remaining} days"
            
            # Extract certificate details
            issuer = dict(x[0] for x in cert['issuer'])
            subject = dict(x[0] for x in cert['subject'])
            
            return {
                'status': 'success' if severity == 'ok' else 'warning',
                'severity': severity,
                'host': host,
                'port': port,
                'certificate': {
                    'subject': subject.get('commonName', 'Unknown'),
                    'issuer': issuer.get('commonName', 'Unknown'),
                    'issued_date': cert['notBefore'],
                    'expiry_date': not_after,
                    'days_remaining': days_remaining,
                    'san': self._extract_san(cert)
                },
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        
        except ssl.SSLError as e:
            return {
                'status': 'failed',
                'severity': 'critical',
                'host': host,
                'port': port,
                'error': f"SSL Error: {str(e)}",
                'message': f"SSL certificate error for {host}",
                'timestamp': datetime.now().isoformat()
            }
        
        except socket.timeout:
            return {
                'status': 'failed',
                'severity': 'error',
                'host': host,
                'port': port,
                'error': 'Connection timeout',
                'message': f"Connection to {host}:{port} timed out",
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'severity': 'error',
                'host': host,
                'port': port,
                'error': str(e),
                'message': f"Failed to check SSL certificate for {host}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_san(self, cert):
        """Extract Subject Alternative Names from certificate"""
        try:
            san_list = []
            for ext in cert.get('subjectAltName', []):
                if ext[0] == 'DNS':
                    san_list.append(ext[1])
            return san_list
        except:
            return []
    
    def check_multiple(self, hosts):
        """
        Check multiple hosts
        
        Args:
            hosts (list): List of (host, port) tuples or host strings
        
        Returns:
            dict: Results keyed by host
        """
        results = {}
        for host_info in hosts:
            if isinstance(host_info, tuple):
                host, port = host_info
            else:
                host = host_info
                port = 443
            
            results[host] = self.check(host, port)
        
        return results
    
    def get_expiring_certificates(self, hosts, days=30):
        """
        Get list of certificates expiring soon
        
        Args:
            hosts (list): Hosts to check
            days (int): Days threshold
        
        Returns:
            list: Certificates expiring within threshold
        """
        expiring = []
        results = self.check_multiple(hosts)
        
        for host, result in results.items():
            if result['status'] in ['warning', 'failed']:
                if 'certificate' in result:
                    if result['certificate']['days_remaining'] <= days:
                        expiring.append({
                            'host': host,
                            **result
                        })
                else:
                    # Include failed checks
                    expiring.append({
                        'host': host,
                        **result
                    })
        
        return expiring

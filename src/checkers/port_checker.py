"""
Port Checker - TCP port connectivity verification.
"""

import socket
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PortChecker:
    """Performs TCP port connectivity checks."""
    
    def __init__(self, timeout: int = 5) -> None:
        """
        Initialize port checker.
        
        Args:
            timeout: Maximum time to wait for connection in seconds
        """
        self.timeout = timeout
        
    def check(self, host: str, port: int) -> Dict[str, Any]:
        """
        Perform port connectivity check.
        
        Args:
            host: Target hostname or IP address
            port: TCP port number to check
            
        Returns:
            Dictionary containing check results:
                - status: 'ok' or 'fail'
                - response_time_ms: Connection time in milliseconds (None if failed)
                - error: Error message if check failed
        """
        logger.info(f"Checking port {port} on {host}")
        
        sock = None
        try:
            start_time = time.time()
            
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Attempt connection
            result = sock.connect_ex((host, port))
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if result == 0:
                logger.debug(f"Port {port} on {host} is open ({elapsed_ms:.2f}ms)")
                return {
                    'status': 'ok',
                    'response_time_ms': round(elapsed_ms, 2),
                    'error': None
                }
            else:
                error_msg = f"Port closed or connection refused"
                logger.warning(f"Port {port} on {host} check failed: {error_msg}")
                return {
                    'status': 'fail',
                    'response_time_ms': None,
                    'error': error_msg
                }
                
        except socket.timeout:
            error_msg = f"Connection timeout after {self.timeout}s"
            logger.warning(f"Port {port} on {host} timed out")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': error_msg
            }
            
        except socket.gaierror as e:
            error_msg = f"Hostname resolution failed: {str(e)}"
            logger.error(f"Cannot resolve {host}: {error_msg}")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error checking port {port} on {host}: {error_msg}")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': error_msg
            }
            
        finally:
            if sock:
                sock.close()

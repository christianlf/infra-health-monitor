"""
Ping Checker - ICMP connectivity verification.
"""

import platform
import subprocess
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PingChecker:
    """Performs ICMP ping checks to verify host availability."""
    
    def __init__(self, timeout: int = 5) -> None:
        """
        Initialize ping checker.
        
        Args:
            timeout: Maximum time to wait for response in seconds
        """
        self.timeout = timeout
        self.system = platform.system().lower()
        
    def check(self, host: str) -> Dict[str, Any]:
        """
        Perform ping check on specified host.
        
        Args:
            host: Target hostname or IP address
            
        Returns:
            Dictionary containing check results:
                - status: 'ok' or 'fail'
                - response_time_ms: Response time in milliseconds (None if failed)
                - error: Error message if check failed
        """
        logger.info(f"Performing ping check on {host}")
        
        try:
            start_time = time.time()
            
            # Build ping command based on OS
            if self.system == 'windows':
                # Windows: ping -n 1 -w timeout_ms host
                command = ['ping', '-n', '1', '-w', str(self.timeout * 1000), host]
            else:
                # Linux/Mac: ping -c 1 -W timeout host
                command = ['ping', '-c', '1', '-W', str(self.timeout), host]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout + 1,
                text=True
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                logger.debug(f"Ping to {host} successful ({elapsed_ms:.2f}ms)")
                return {
                    'status': 'ok',
                    'response_time_ms': round(elapsed_ms, 2),
                    'error': None
                }
            else:
                error_msg = f"Host unreachable or no response"
                logger.warning(f"Ping to {host} failed: {error_msg}")
                return {
                    'status': 'fail',
                    'response_time_ms': None,
                    'error': error_msg
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout after {self.timeout}s"
            logger.warning(f"Ping to {host} timed out")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error pinging {host}: {error_msg}")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': error_msg
            }

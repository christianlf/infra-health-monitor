"""
Port Checker - TCP port connectivity verification with retry logic.

MELHORIAS IMPLEMENTADAS:
- Retry logic com backoff exponencial (3 tentativas)
- Melhor tratamento de timeouts
- Registro de tentativas no resultado
"""

import socket
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PortChecker:
    """Performs TCP port connectivity checks with retry logic."""
    
    def __init__(self, timeout: int = 5, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """
        Initialize port checker with retry configuration.
        
        Args:
            timeout: Maximum time to wait for connection in seconds
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _single_check(self, host: str, port: int) -> Dict[str, Any]:
        """
        Perform a single port check without retry logic.
        
        Args:
            host: Target hostname or IP address
            port: TCP port number to check
            
        Returns:
            Dictionary with check results
        """
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
                return {
                    'status': 'ok',
                    'response_time_ms': round(elapsed_ms, 2),
                    'error': None
                }
            else:
                return {
                    'status': 'fail',
                    'response_time_ms': None,
                    'error': "Port closed or connection refused"
                }
                
        except socket.timeout:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Connection timeout after {self.timeout}s"
            }
            
        except socket.gaierror as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Hostname resolution failed: {str(e)}"
            }
            
        except Exception as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Unexpected error: {str(e)}"
            }
            
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def check(self, host: str, port: int) -> Dict[str, Any]:
        """
        Perform port connectivity check with retry logic to avoid false positives.
        
        RETRY LOGIC:
        - Attempts check up to max_retries times
        - Waits retry_delay * (attempt_number) between attempts (exponential backoff)
        - Returns success immediately on first successful attempt
        - Returns failure only if all attempts fail
        
        Args:
            host: Target hostname or IP address
            port: TCP port number to check
            
        Returns:
            Dictionary containing check results:
                - status: 'ok' or 'fail'
                - response_time_ms: Connection time in milliseconds (None if failed)
                - error: Error message if check failed
                - attempts: Number of attempts made
                - retry_count: Number of retries performed
        """
        logger.info(f"Checking port {port} on {host} (max {self.max_retries} attempts)")
        
        # Validate port number
        if not isinstance(port, int) or port < 1 or port > 65535:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Invalid port number: {port}",
                'attempts': 0,
                'retry_count': 0
            }
        
        # Retry loop with exponential backoff
        last_result = None
        for attempt in range(1, self.max_retries + 1):
            last_result = self._single_check(host, port)
            
            if last_result['status'] == 'ok':
                logger.debug(f"Port {port} on {host} is open (attempt {attempt}, "
                           f"{last_result['response_time_ms']:.2f}ms)")
                last_result['attempts'] = attempt
                last_result['retry_count'] = attempt - 1
                return last_result
            
            # If not the last attempt, wait before retry with exponential backoff
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt
                logger.debug(f"Port check attempt {attempt} to {host}:{port} failed, "
                           f"retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        # All attempts failed
        logger.warning(f"Port {port} on {host} check failed after {self.max_retries} attempts: "
                      f"{last_result['error']}")
        last_result['attempts'] = self.max_retries
        last_result['retry_count'] = self.max_retries - 1
        return last_result

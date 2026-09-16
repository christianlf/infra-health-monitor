"""
Ping Checker - ICMP connectivity verification with retry logic and input sanitization.

MELHORIAS IMPLEMENTADAS:
- Retry logic com backoff exponencial (3 tentativas)
- Input sanitization para prevenir command injection
- Validação de hostname/IP usando ipaddress e regex
- Registro de tentativas no resultado
"""

import platform
import subprocess
import time
import logging
import re
import ipaddress
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Regex para validar hostnames válidos (RFC 1123)
HOSTNAME_PATTERN = re.compile(
    r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63}(?<!-))*\.?$'
)


class PingChecker:
    """Performs ICMP ping checks to verify host availability with retry logic."""
    
    def __init__(self, timeout: int = 5, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """
        Initialize ping checker with retry configuration.
        
        Args:
            timeout: Maximum time to wait for response in seconds
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.system = platform.system().lower()
    
    def _validate_host(self, host: str) -> bool:
        """
        Validate that host is a safe IP address or hostname.
        Prevents command injection attacks.
        
        Args:
            host: Hostname or IP address to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Try to parse as IP address first (v4 or v6)
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            pass
        
        # Validate as hostname using regex
        if HOSTNAME_PATTERN.match(host):
            return True
        
        logger.warning(f"Invalid host format rejected: {host}")
        return False
    
    def _single_ping(self, host: str) -> Dict[str, Any]:
        """
        Perform a single ping check without retry logic.
        
        Args:
            host: Target hostname or IP address (already validated)
            
        Returns:
            Dictionary with check results
        """
        try:
            start_time = time.time()
            
            # Build ping command based on OS
            # SECURITY: Using list format (not shell=True) prevents shell injection
            if self.system == 'windows':
                # Windows: ping -n 1 -w timeout_ms host
                command = ['ping', '-n', '1', '-w', str(self.timeout * 1000), host]
            else:
                # Linux/Mac: ping -c 1 -W timeout host
                command = ['ping', '-c', '1', '-W', str(self.timeout), host]
            
            # SECURITY: shell=False (default) prevents command injection
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout + 1,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                return {
                    'status': 'ok',
                    'response_time_ms': round(elapsed_ms, 2),
                    'error': None
                }
            else:
                return {
                    'status': 'fail',
                    'response_time_ms': None,
                    'error': "Host unreachable or no response"
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Timeout after {self.timeout}s"
            }
            
        except Exception as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def check(self, host: str) -> Dict[str, Any]:
        """
        Perform ping check with retry logic to avoid false positives.
        
        RETRY LOGIC:
        - Attempts check up to max_retries times
        - Waits retry_delay * (attempt_number) between attempts (exponential backoff)
        - Returns success immediately on first successful attempt
        - Returns failure only if all attempts fail
        
        Args:
            host: Target hostname or IP address
            
        Returns:
            Dictionary containing check results:
                - status: 'ok' or 'fail'
                - response_time_ms: Response time in milliseconds (None if failed)
                - error: Error message if check failed
                - attempts: Number of attempts made
                - retry_count: Number of retries performed
        """
        logger.info(f"Performing ping check on {host} (max {self.max_retries} attempts)")
        
        # SECURITY: Validate input before using in system command
        if not self._validate_host(host):
            return {
                'status': 'fail',
                'response_time_ms': None,
                'error': f"Invalid hostname or IP address: {host}",
                'attempts': 0,
                'retry_count': 0
            }
        
        # Retry loop with exponential backoff
        last_result = None
        for attempt in range(1, self.max_retries + 1):
            last_result = self._single_ping(host)
            
            if last_result['status'] == 'ok':
                logger.debug(f"Ping to {host} successful on attempt {attempt} "
                           f"({last_result['response_time_ms']:.2f}ms)")
                last_result['attempts'] = attempt
                last_result['retry_count'] = attempt - 1
                return last_result
            
            # If not the last attempt, wait before retry with exponential backoff
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt
                logger.debug(f"Ping attempt {attempt} to {host} failed, "
                           f"retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        # All attempts failed
        logger.warning(f"Ping to {host} failed after {self.max_retries} attempts: "
                      f"{last_result['error']}")
        last_result['attempts'] = self.max_retries
        last_result['retry_count'] = self.max_retries - 1
        return last_result

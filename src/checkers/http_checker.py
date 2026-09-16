"""
HTTP Checker - HTTP/HTTPS endpoint verification with retry logic.

MELHORIAS IMPLEMENTADAS:
- Retry logic com backoff exponencial (3 tentativas)
- Tratamento robusto de erros de conexão
- Registro de tentativas no resultado
"""

import time
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class HTTPChecker:
    """Performs HTTP/HTTPS endpoint health checks with retry logic."""
    
    def __init__(self, timeout: int = 5, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """
        Initialize HTTP checker with retry configuration.
        
        Args:
            timeout: Maximum time to wait for HTTP response in seconds
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _single_check(self, url: str, expected_status: int) -> Dict[str, Any]:
        """
        Perform a single HTTP check without retry logic.
        
        Args:
            url: Target URL to check
            expected_status: Expected HTTP status code
            
        Returns:
            Dictionary with check results
        """
        try:
            start_time = time.time()
            
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'InfraHealthMonitor/2.0'},
                verify=True  # Verify SSL certificates
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == expected_status:
                return {
                    'status': 'ok',
                    'response_time_ms': round(elapsed_ms, 2),
                    'http_status': response.status_code,
                    'error': None
                }
            else:
                return {
                    'status': 'fail',
                    'response_time_ms': round(elapsed_ms, 2),
                    'http_status': response.status_code,
                    'error': f"Unexpected status code {response.status_code} (expected {expected_status})"
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': f"Request timeout after {self.timeout}s"
            }
            
        except requests.exceptions.ConnectionError as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': f"Connection error: {str(e)}"
            }
            
        except requests.exceptions.SSLError as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': f"SSL certificate error: {str(e)}"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': f"Request error: {str(e)}"
            }
            
        except Exception as e:
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def check(self, url: str, expected_status: Optional[int] = 200) -> Dict[str, Any]:
        """
        Perform HTTP endpoint check with retry logic to avoid false positives.
        
        RETRY LOGIC:
        - Attempts check up to max_retries times
        - Waits retry_delay * (attempt_number) between attempts (exponential backoff)
        - Returns success immediately on first successful attempt
        - Returns failure only if all attempts fail
        
        Args:
            url: Target URL to check
            expected_status: Expected HTTP status code (default: 200)
            
        Returns:
            Dictionary containing check results:
                - status: 'ok' or 'fail'
                - response_time_ms: Response time in milliseconds (None if failed)
                - http_status: HTTP status code received (None if request failed)
                - error: Error message if check failed
                - attempts: Number of attempts made
                - retry_count: Number of retries performed
        """
        logger.info(f"Checking HTTP endpoint {url} (max {self.max_retries} attempts)")
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': f"Invalid URL format: must start with http:// or https://",
                'attempts': 0,
                'retry_count': 0
            }
        
        # Retry loop with exponential backoff
        last_result = None
        for attempt in range(1, self.max_retries + 1):
            last_result = self._single_check(url, expected_status)
            
            if last_result['status'] == 'ok':
                logger.debug(f"HTTP check for {url} successful (attempt {attempt}, "
                           f"status: {last_result['http_status']}, "
                           f"{last_result['response_time_ms']:.2f}ms)")
                last_result['attempts'] = attempt
                last_result['retry_count'] = attempt - 1
                return last_result
            
            # If not the last attempt, wait before retry with exponential backoff
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt
                logger.debug(f"HTTP check attempt {attempt} to {url} failed, "
                           f"retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        # All attempts failed
        logger.warning(f"HTTP check for {url} failed after {self.max_retries} attempts: "
                      f"{last_result['error']}")
        last_result['attempts'] = self.max_retries
        last_result['retry_count'] = self.max_retries - 1
        return last_result

"""
HTTP Checker - HTTP/HTTPS endpoint verification.
"""

import time
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class HTTPChecker:
    """Performs HTTP/HTTPS endpoint health checks."""
    
    def __init__(self, timeout: int = 5) -> None:
        """
        Initialize HTTP checker.
        
        Args:
            timeout: Maximum time to wait for HTTP response in seconds
        """
        self.timeout = timeout
        
    def check(self, url: str, expected_status: Optional[int] = 200) -> Dict[str, Any]:
        """
        Perform HTTP endpoint check.
        
        Args:
            url: Target URL to check
            expected_status: Expected HTTP status code (default: 200)
            
        Returns:
            Dictionary containing check results:
                - status: 'ok' or 'fail'
                - response_time_ms: Response time in milliseconds (None if failed)
                - http_status: HTTP status code received (None if request failed)
                - error: Error message if check failed
        """
        logger.info(f"Checking HTTP endpoint {url}")
        
        try:
            start_time = time.time()
            
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'InfraHealthMonitor/1.0'}
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == expected_status:
                logger.debug(
                    f"HTTP check for {url} successful "
                    f"(status: {response.status_code}, {elapsed_ms:.2f}ms)"
                )
                return {
                    'status': 'ok',
                    'response_time_ms': round(elapsed_ms, 2),
                    'http_status': response.status_code,
                    'error': None
                }
            else:
                error_msg = (
                    f"Unexpected status code {response.status_code} "
                    f"(expected {expected_status})"
                )
                logger.warning(f"HTTP check for {url} failed: {error_msg}")
                return {
                    'status': 'fail',
                    'response_time_ms': round(elapsed_ms, 2),
                    'http_status': response.status_code,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.warning(f"HTTP check for {url} timed out")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': error_msg
            }
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Connection error for {url}: {error_msg}")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': error_msg
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Request error for {url}: {error_msg}")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error checking {url}: {error_msg}")
            return {
                'status': 'fail',
                'response_time_ms': None,
                'http_status': None,
                'error': error_msg
            }

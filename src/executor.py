"""
Parallel Execution Module - Concurrent health check execution for better performance.

MELHORIAS IMPLEMENTADAS:
- ThreadPoolExecutor para execução paralela de checks
- Redução drástica do tempo total quando monitorando múltiplos alvos
- Thread-safe logging e database operations
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable
from src.config import config
from src.checkers.ping_checker import PingChecker
from src.checkers.port_checker import PortChecker
from src.checkers.http_checker import HTTPChecker

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """Executes health checks in parallel using thread pool."""
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum number of concurrent threads (default: 10)
        """
        self.max_workers = max_workers
        self.timeout = config.default_timeout
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
    
    def _create_checker(self, target_type: str):
        """Create appropriate checker instance based on type."""
        if target_type == 'ping':
            return PingChecker(
                timeout=self.timeout,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
        elif target_type == 'port':
            return PortChecker(
                timeout=self.timeout,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
        elif target_type == 'http':
            return HTTPChecker(
                timeout=self.timeout,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
        else:
            return None
    
    def _perform_single_check(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform health check on a single target (thread-safe).
        
        Args:
            target: Target configuration dictionary
            
        Returns:
            Check result dictionary
        """
        target_type = target.get('type', '').lower()
        target_name = target.get('name', 'Unknown')
        
        result = {
            'target_name': target_name,
            'target_type': target_type,
            'status': 'fail',
            'response_time_ms': None,
            'error': 'Unknown error',
            'attempts': 0,
            'retry_count': 0
        }
        
        try:
            checker = self._create_checker(target_type)
            
            if not checker:
                result['error'] = f"Unknown target type: {target_type}"
                return result
            
            if target_type == 'ping':
                check_result = checker.check(target.get('host', ''))
                result.update(check_result)
                
            elif target_type == 'port':
                check_result = checker.check(
                    target.get('host', ''),
                    target.get('port', 0)
                )
                result.update(check_result)
                
            elif target_type == 'http':
                check_result = checker.check(
                    target.get('url', ''),
                    target.get('expected_status', 200)
                )
                result.update(check_result)
                if 'http_status' in check_result:
                    result['http_status'] = check_result['http_status']
                    
        except Exception as e:
            logger.error(f"Error checking {target_name}: {e}")
            result['error'] = str(e)
        
        return result
    
    def execute_checks(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute health checks on all targets in parallel.
        
        PERFORMANCE IMPROVEMENT:
        - Sequential: N targets * timeout = 10 targets * 5s = 50s
        - Parallel (10 workers): max(timeout) = ~5s
        
        Args:
            targets: List of target configurations
            
        Returns:
            List of check results (order may differ from input)
        """
        if not targets:
            logger.warning("No targets provided for execution")
            return []
        
        logger.info(f"Executing {len(targets)} checks in parallel (max {self.max_workers} workers)")
        
        results = []
        
        # Use ThreadPoolExecutor for concurrent execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all checks to thread pool
            future_to_target = {
                executor.submit(self._perform_single_check, target): target
                for target in targets
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log result
                    if result['status'] == 'ok':
                        logger.info(f"✓ {result['target_name']}: OK "
                                  f"({result.get('response_time_ms', 0):.0f}ms)")
                    else:
                        logger.warning(f"✗ {result['target_name']}: FAIL - {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Exception for target {target.get('name', 'Unknown')}: {e}")
                    results.append({
                        'target_name': target.get('name', 'Unknown'),
                        'target_type': target.get('type', 'unknown'),
                        'status': 'fail',
                        'response_time_ms': None,
                        'error': f"Execution exception: {str(e)}",
                        'attempts': 0,
                        'retry_count': 0
                    })
        
        logger.info(f"Completed {len(results)}/{len(targets)} checks")
        return results

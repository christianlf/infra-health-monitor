"""
Alert Manager - Handles alert generation and logging.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert generation and notification for health check failures."""
    
    def __init__(self, alert_log_path: str, alert_threshold: int = 3) -> None:
        """
        Initialize alert manager.
        
        Args:
            alert_log_path: Path to alert log file
            alert_threshold: Number of consecutive failures before triggering alert
        """
        self.alert_log_path = alert_log_path
        self.alert_threshold = alert_threshold
        self._ensure_log_file()
        
    def _ensure_log_file(self) -> None:
        """Ensure alert log file exists."""
        log_file = Path(self.alert_log_path)
        if not log_file.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.touch()
            logger.info(f"Created alert log file: {self.alert_log_path}")
    
    def check_and_alert(
        self,
        target_name: str,
        target_type: str,
        consecutive_failures: int,
        last_error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if alert should be triggered and log it.
        
        Args:
            target_name: Name of the target that failed
            target_type: Type of check (ping/port/http)
            consecutive_failures: Number of consecutive failures
            last_error: Last error message
            metadata: Additional context (host, port, url, etc.)
            
        Returns:
            True if alert was triggered, False otherwise
        """
        if consecutive_failures >= self.alert_threshold:
            self._log_alert(
                target_name=target_name,
                target_type=target_type,
                consecutive_failures=consecutive_failures,
                last_error=last_error,
                metadata=metadata
            )
            return True
        return False
    
    def _log_alert(
        self,
        target_name: str,
        target_type: str,
        consecutive_failures: int,
        last_error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Write alert to log file.
        
        Args:
            target_name: Name of the target
            target_type: Type of check
            consecutive_failures: Number of failures
            last_error: Last error message
            metadata: Additional context
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        alert_message = (
            f"[{timestamp}] ALERT: {target_name} ({target_type}) "
            f"- {consecutive_failures} consecutive failures"
        )
        
        if last_error:
            alert_message += f" - Last error: {last_error}"
        
        if metadata:
            details = ", ".join(f"{k}={v}" for k, v in metadata.items())
            alert_message += f" - Details: {details}"
        
        try:
            with open(self.alert_log_path, 'a') as f:
                f.write(alert_message + '\n')
            
            logger.warning(f"Alert triggered: {alert_message}")
            
        except Exception as e:
            logger.error(f"Failed to write alert to log: {e}")
    
    def log_recovery(self, target_name: str, target_type: str) -> None:
        """
        Log when a target recovers from failure.
        
        Args:
            target_name: Name of the target
            target_type: Type of check
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        recovery_message = (
            f"[{timestamp}] RECOVERY: {target_name} ({target_type}) "
            f"- Service back online"
        )
        
        try:
            with open(self.alert_log_path, 'a') as f:
                f.write(recovery_message + '\n')
            
            logger.info(f"Recovery logged: {recovery_message}")
            
        except Exception as e:
            logger.error(f"Failed to write recovery to log: {e}")
    
    def get_recent_alerts(self, lines: int = 50) -> list:
        """
        Get recent alerts from log file.
        
        Args:
            lines: Number of recent lines to retrieve
            
        Returns:
            List of alert log lines
        """
        try:
            with open(self.alert_log_path, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
                
        except FileNotFoundError:
            logger.warning(f"Alert log file not found: {self.alert_log_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading alert log: {e}")
            return []

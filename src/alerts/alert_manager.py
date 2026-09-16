"""
Alert Manager - Handles alert generation, logging and webhook notifications.

MELHORIAS IMPLEMENTADAS:
- Suporte a webhooks HTTP (Discord, Slack, Microsoft Teams)
- Fallback graceful se webhook falhar (continua com log local)
- Configuração via variável de ambiente ALERT_WEBHOOK_URL
- Tratamento robusto de erros de rede
"""

import logging
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert generation, notification and logging for health check failures."""
    
    def __init__(
        self,
        alert_log_path: str,
        alert_threshold: int = 3,
        webhook_url: Optional[str] = None,
        webhook_timeout: int = 5
    ) -> None:
        """
        Initialize alert manager with webhook support.
        
        Args:
            alert_log_path: Path to alert log file
            alert_threshold: Number of consecutive failures before triggering alert
            webhook_url: Optional webhook URL for external notifications (Discord/Slack/Teams)
            webhook_timeout: Timeout for webhook requests in seconds
        """
        self.alert_log_path = alert_log_path
        self.alert_threshold = alert_threshold
        self.webhook_url = webhook_url
        self.webhook_timeout = webhook_timeout
        self._ensure_log_file()
        
        if self.webhook_url:
            logger.info(f"Alert manager initialized with webhook: {self._mask_url(self.webhook_url)}")
        else:
            logger.info("Alert manager initialized (webhook disabled)")
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of webhook URL for logging."""
        if not url:
            return "None"
        # Show only protocol and domain, hide path/tokens
        parts = url.split('/')
        if len(parts) >= 3:
            return f"{parts[0]}//{parts[2]}/***"
        return "***"
    
    def _ensure_log_file(self) -> None:
        """Ensure alert log file exists."""
        log_file = Path(self.alert_log_path)
        if not log_file.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.touch()
            logger.info(f"Created alert log file: {self.alert_log_path}")
    
    def _send_webhook(self, message: str, alert_type: str = "alert") -> bool:
        """
        Send notification to webhook endpoint.
        
        WEBHOOK FORMATS SUPPORTED:
        - Discord: {"content": "message"}
        - Slack: {"text": "message"}
        - Microsoft Teams: {"text": "message"}
        - Generic: {"message": "message", "type": "alert"}
        
        Args:
            message: Alert message to send
            alert_type: Type of alert ("alert" or "recovery")
            
        Returns:
            True if webhook sent successfully, False otherwise
        """
        if not self.webhook_url:
            return False
        
        try:
            # Build payload compatible with multiple platforms
            payload = {
                "content": message,  # Discord format
                "text": message,     # Slack/Teams format
                "message": message,  # Generic format
                "type": alert_type,
                "timestamp": datetime.now().isoformat()
            }
            
            # RESILIENCE: Don't let webhook failure crash the main process
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.webhook_timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in (200, 204):
                logger.debug(f"Webhook notification sent successfully ({response.status_code})")
                return True
            else:
                logger.warning(f"Webhook returned status {response.status_code}: {response.text[:100]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Webhook request timed out after {self.webhook_timeout}s")
            return False
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Webhook connection failed: {str(e)}")
            return False
            
        except Exception as e:
            # RESILIENCE: Catch all exceptions to prevent webhook issues from breaking monitoring
            logger.error(f"Webhook notification failed: {str(e)}")
            return False
    
    def check_and_alert(
        self,
        target_name: str,
        target_type: str,
        consecutive_failures: int,
        last_error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if alert should be triggered and send notifications.
        
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
            self._trigger_alert(
                target_name=target_name,
                target_type=target_type,
                consecutive_failures=consecutive_failures,
                last_error=last_error,
                metadata=metadata
            )
            return True
        return False
    
    def _trigger_alert(
        self,
        target_name: str,
        target_type: str,
        consecutive_failures: int,
        last_error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trigger alert: log to file AND send webhook if configured.
        
        Args:
            target_name: Name of the target
            target_type: Type of check
            consecutive_failures: Number of failures
            last_error: Last error message
            metadata: Additional context
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build alert message
        alert_message = (
            f"🚨 ALERT: {target_name} ({target_type}) "
            f"- {consecutive_failures} consecutive failures"
        )
        
        if last_error:
            alert_message += f"\n   Error: {last_error}"
        
        if metadata:
            details = ", ".join(f"{k}={v}" for k, v in metadata.items())
            alert_message += f"\n   Details: {details}"
        
        # Log to file (primary notification method)
        log_message = f"[{timestamp}] {alert_message}"
        try:
            with open(self.alert_log_path, 'a') as f:
                f.write(log_message + '\n')
            logger.warning(f"Alert triggered: {log_message}")
        except Exception as e:
            logger.error(f"Failed to write alert to log: {e}")
        
        # Send webhook notification (secondary notification method)
        if self.webhook_url:
            webhook_sent = self._send_webhook(alert_message, alert_type="alert")
            if webhook_sent:
                logger.info(f"Alert notification sent via webhook for {target_name}")
            else:
                logger.warning(f"Webhook notification failed for {target_name} (logged locally)")
    
    def log_recovery(self, target_name: str, target_type: str) -> None:
        """
        Log when a target recovers from failure and send webhook if configured.
        
        Args:
            target_name: Name of the target
            target_type: Type of check
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        recovery_message = (
            f"✅ RECOVERY: {target_name} ({target_type}) - Service back online"
        )
        
        # Log to file
        log_message = f"[{timestamp}] {recovery_message}"
        try:
            with open(self.alert_log_path, 'a') as f:
                f.write(log_message + '\n')
            logger.info(f"Recovery logged: {log_message}")
        except Exception as e:
            logger.error(f"Failed to write recovery to log: {e}")
        
        # Send webhook notification
        if self.webhook_url:
            webhook_sent = self._send_webhook(recovery_message, alert_type="recovery")
            if webhook_sent:
                logger.info(f"Recovery notification sent via webhook for {target_name}")
    
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

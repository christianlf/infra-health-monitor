"""
Configuration module for Infrastructure Health Monitor.
Loads settings from environment variables and provides centralized access.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class that loads and validates environment settings."""
    
    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.default_timeout: int = int(os.getenv('DEFAULT_TIMEOUT', '5'))
        self.alert_threshold: int = int(os.getenv('ALERT_THRESHOLD', '3'))
        self.database_path: str = os.getenv('DATABASE_PATH', 'health_monitor.db')
        self.alert_log_path: str = os.getenv('ALERT_LOG_PATH', 'alerts.log')
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.alert_webhook_url: Optional[str] = os.getenv('ALERT_WEBHOOK_URL')
        
        # Retry logic configuration
        self.max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay: float = float(os.getenv('RETRY_DELAY', '1.0'))
        
    def __repr__(self) -> str:
        """String representation of configuration (hiding sensitive data)."""
        webhook_status = "configured" if self.alert_webhook_url else "not configured"
        return (
            f"Config(timeout={self.default_timeout}, "
            f"alert_threshold={self.alert_threshold}, "
            f"max_retries={self.max_retries}, "
            f"database={self.database_path}, "
            f"log_level={self.log_level}, "
            f"webhook={webhook_status})"
        )


# Global configuration instance
config = Config()

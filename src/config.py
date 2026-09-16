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
        
    def __repr__(self) -> str:
        """String representation of configuration (hiding sensitive data)."""
        return (
            f"Config(timeout={self.default_timeout}, "
            f"alert_threshold={self.alert_threshold}, "
            f"database={self.database_path}, "
            f"log_level={self.log_level})"
        )


# Global configuration instance
config = Config()

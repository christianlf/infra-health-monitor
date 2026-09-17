#!/usr/bin/env python3
"""
Dashboard Server Launcher
Starts the web dashboard for real-time monitoring
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.dashboard.web_server import DashboardServer
from src.config import Config


if __name__ == '__main__':
    print("🚀 Starting Infrastructure Health Monitor Dashboard...")
    
    # Load config
    config = Config()
    
    # Start dashboard server
    server = DashboardServer(
        database_path=config.database_path,
        host='0.0.0.0',
        port=8080
    )
    
    server.run()

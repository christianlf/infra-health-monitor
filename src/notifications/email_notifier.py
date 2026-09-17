"""
Email Notification System
Sends email alerts via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os


class EmailNotifier:
    """
    Send email notifications for infrastructure alerts
    
    Supports:
    - Gmail SMTP
    - Office 365 SMTP
    - Custom SMTP servers
    """
    
    def __init__(self, smtp_config=None):
        """
        Initialize email notifier
        
        smtp_config format:
        {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': 'alerts@example.com',
            'smtp_password': 'your_password',
            'smtp_from': 'InfraHealthMonitor <alerts@example.com>',
            'smtp_to': ['admin@example.com', 'team@example.com']
        }
        """
        if smtp_config is None:
            # Load from environment variables
            smtp_config = self._load_from_env()
        
        self.config = smtp_config
        self.enabled = self._validate_config()
    
    def _load_from_env(self):
        """Load SMTP configuration from environment variables"""
        return {
            'smtp_host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_user': os.getenv('SMTP_USER', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'smtp_from': os.getenv('SMTP_FROM', 'InfraHealthMonitor <alerts@example.com>'),
            'smtp_to': os.getenv('SMTP_TO', '').split(',') if os.getenv('SMTP_TO') else [],
            'smtp_use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
    
    def _validate_config(self):
        """Validate SMTP configuration"""
        required = ['smtp_host', 'smtp_user', 'smtp_password']
        for field in required:
            if not self.config.get(field):
                print(f"⚠️ Email notifications disabled: Missing {field}")
                return False
        
        if not self.config.get('smtp_to'):
            print("⚠️ Email notifications disabled: No recipients configured")
            return False
        
        return True
    
    def send_alert(self, target, status, details):
        """
        Send alert email
        
        Args:
            target (str): Target name
            status (str): 'down' or 'recovered'
            details (dict): Additional details
        """
        if not self.enabled:
            return False
        
        try:
            subject, body = self._format_alert(target, status, details)
            self._send_email(subject, body)
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_daily_summary(self, summary_data):
        """Send daily summary email"""
        if not self.enabled:
            return False
        
        try:
            subject = f"📊 Daily Infrastructure Health Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = self._format_summary(summary_data)
            self._send_email(subject, body)
            return True
        except Exception as e:
            print(f"❌ Failed to send summary email: {e}")
            return False
    
    def _format_alert(self, target, status, details):
        """Format alert email content"""
        if status == 'down':
            subject = f"🚨 ALERT: {target} is DOWN"
            body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert {{ background-color: #fff5f5; border-left: 4px solid #f56565; padding: 15px; margin: 20px 0; }}
        .info {{ background-color: #f7fafc; padding: 10px; margin: 10px 0; }}
        .label {{ font-weight: bold; color: #2d3748; }}
    </style>
</head>
<body>
    <h2 style="color: #c53030;">🚨 Infrastructure Alert</h2>
    
    <div class="alert">
        <p><span class="label">Target:</span> {target}</p>
        <p><span class="label">Status:</span> <strong>OFFLINE</strong></p>
        <p><span class="label">Time:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="info">
        <p><span class="label">Host:</span> {details.get('host', 'N/A')}</p>
        <p><span class="label">Type:</span> {details.get('type', 'N/A')}</p>
        <p><span class="label">Consecutive Failures:</span> {details.get('consecutive_failures', 'N/A')}</p>
        <p><span class="label">Error:</span> {details.get('error', 'Unknown error')}</p>
    </div>
    
    <p style="color: #718096; font-size: 0.9em;">
        This is an automated alert from Infrastructure Health Monitor.
    </p>
</body>
</html>
            """
        else:  # recovered
            subject = f"✅ RECOVERED: {target} is back online"
            body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .recovered {{ background-color: #f0fff4; border-left: 4px solid #48bb78; padding: 15px; margin: 20px 0; }}
        .info {{ background-color: #f7fafc; padding: 10px; margin: 10px 0; }}
        .label {{ font-weight: bold; color: #2d3748; }}
    </style>
</head>
<body>
    <h2 style="color: #38a169;">✅ Service Recovered</h2>
    
    <div class="recovered">
        <p><span class="label">Target:</span> {target}</p>
        <p><span class="label">Status:</span> <strong>ONLINE</strong></p>
        <p><span class="label">Time:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="info">
        <p><span class="label">Downtime:</span> {details.get('downtime', 'N/A')}</p>
        <p><span class="label">Latency:</span> {details.get('latency_ms', 'N/A')}ms</p>
    </div>
    
    <p style="color: #718096; font-size: 0.9em;">
        This is an automated recovery notification from Infrastructure Health Monitor.
    </p>
</body>
</html>
            """
        
        return subject, body
    
    def _format_summary(self, summary_data):
        """Format daily summary email"""
        targets_html = ""
        for target, stats in summary_data.get('targets', {}).items():
            color = "#48bb78" if stats['uptime_percent'] >= 99 else "#f6ad55" if stats['uptime_percent'] >= 95 else "#f56565"
            targets_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{target}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{stats['total_checks']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{stats['successful']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{stats['failed']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: {color}; font-weight: bold;">{stats['uptime_percent']:.2f}%</td>
            </tr>
            """
        
        body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .summary {{ background-color: #f7fafc; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background-color: #2d3748; color: white; padding: 12px; text-align: left; }}
    </style>
</head>
<body>
    <h2 style="color: #2d3748;">📊 Daily Infrastructure Health Report</h2>
    
    <div class="summary">
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        <p><strong>Total Checks:</strong> {summary_data.get('total_checks', 0)}</p>
        <p><strong>Overall Uptime:</strong> {summary_data.get('overall_uptime', 0):.2f}%</p>
    </div>
    
    <h3>Per-Target Statistics</h3>
    <table>
        <thead>
            <tr>
                <th>Target</th>
                <th>Checks</th>
                <th>Successful</th>
                <th>Failed</th>
                <th>Uptime</th>
            </tr>
        </thead>
        <tbody>
            {targets_html}
        </tbody>
    </table>
    
    <p style="color: #718096; font-size: 0.9em; margin-top: 20px;">
        Generated by Infrastructure Health Monitor
    </p>
</body>
</html>
        """
        
        return body
    
    def _send_email(self, subject, body):
        """Send email via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.config['smtp_from']
        msg['To'] = ', '.join(self.config['smtp_to'])
        
        # Attach HTML body
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Connect and send
        with smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port']) as server:
            if self.config.get('smtp_use_tls', True):
                server.starttls()
            
            server.login(self.config['smtp_user'], self.config['smtp_password'])
            server.send_message(msg)
    
    def test_connection(self):
        """Test SMTP connection"""
        if not self.enabled:
            return False, "Email notifications not configured"
        
        try:
            with smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port']) as server:
                if self.config.get('smtp_use_tls', True):
                    server.starttls()
                server.login(self.config['smtp_user'], self.config['smtp_password'])
            return True, "SMTP connection successful"
        except Exception as e:
            return False, f"SMTP connection failed: {str(e)}"

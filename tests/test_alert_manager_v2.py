"""
Unit tests for AlertManager with webhook support.

TESTES IMPLEMENTADOS:
- Mock de requests.post para evitar chamadas HTTP reais
- Validação de webhook notifications
- Fallback graceful quando webhook falha
- Resiliência: webhook failure não interrompe monitoramento
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os
from src.alerts.alert_manager import AlertManager


class TestAlertManagerWithWebhook(unittest.TestCase):
    """Test cases for AlertManager with webhook support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
        self.temp_log.close()
        self.log_path = self.temp_log.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.log_path):
            os.unlink(self.log_path)
    
    def test_alert_without_webhook(self):
        """Test alert generation without webhook (local log only)."""
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3,
            webhook_url=None
        )
        
        triggered = alert_mgr.check_and_alert(
            target_name='Test Server',
            target_type='ping',
            consecutive_failures=3,
            last_error='Host unreachable'
        )
        
        self.assertTrue(triggered)
        
        # Verify alert was logged to file
        with open(self.log_path, 'r') as f:
            log_content = f.read()
            self.assertIn('ALERT', log_content)
            self.assertIn('Test Server', log_content)
            self.assertIn('3 consecutive failures', log_content)
    
    @patch('src.alerts.alert_manager.requests.post')
    def test_alert_with_webhook_success(self, mock_post):
        """Test alert generation with successful webhook delivery."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3,
            webhook_url='https://hooks.example.com/webhook/test123'
        )
        
        triggered = alert_mgr.check_and_alert(
            target_name='Test Server',
            target_type='http',
            consecutive_failures=3,
            last_error='Connection timeout',
            metadata={'url': 'https://api.example.com'}
        )
        
        self.assertTrue(triggered)
        
        # Verify webhook was called
        self.assertEqual(mock_post.call_count, 1)
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertIn('content', payload)
        self.assertIn('Test Server', payload['content'])
        self.assertEqual(payload['type'], 'alert')
        
        # Verify alert was also logged locally
        with open(self.log_path, 'r') as f:
            log_content = f.read()
            self.assertIn('ALERT', log_content)
    
    @patch('src.alerts.alert_manager.requests.post')
    def test_webhook_failure_does_not_crash(self, mock_post):
        """Test that webhook failure doesn't prevent local logging (resilience)."""
        # Simulate webhook timeout
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3,
            webhook_url='https://hooks.example.com/webhook/test123'
        )
        
        # This should NOT raise an exception even though webhook fails
        try:
            triggered = alert_mgr.check_and_alert(
                target_name='Test Server',
                target_type='ping',
                consecutive_failures=3,
                last_error='Host down'
            )
            success = True
        except Exception:
            success = False
        
        self.assertTrue(success)
        self.assertTrue(triggered)
        
        # Verify local log still works
        with open(self.log_path, 'r') as f:
            log_content = f.read()
            self.assertIn('ALERT', log_content)
    
    @patch('src.alerts.alert_manager.requests.post')
    def test_webhook_connection_error_handled(self, mock_post):
        """Test graceful handling of webhook connection errors."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError('Network unreachable')
        
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3,
            webhook_url='https://hooks.example.com/webhook/test123'
        )
        
        # Should not crash
        triggered = alert_mgr.check_and_alert(
            target_name='Test Server',
            target_type='port',
            consecutive_failures=5
        )
        
        self.assertTrue(triggered)
    
    @patch('src.alerts.alert_manager.requests.post')
    def test_recovery_notification_with_webhook(self, mock_post):
        """Test recovery notifications are sent via webhook."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3,
            webhook_url='https://hooks.example.com/webhook/test123'
        )
        
        alert_mgr.log_recovery('Test Server', 'http')
        
        # Verify webhook was called for recovery
        self.assertEqual(mock_post.call_count, 1)
        
        payload = mock_post.call_args[1]['json']
        self.assertIn('RECOVERY', payload['content'])
        self.assertEqual(payload['type'], 'recovery')
        
        # Verify local log
        with open(self.log_path, 'r') as f:
            log_content = f.read()
            self.assertIn('RECOVERY', log_content)
    
    def test_alert_threshold_not_met(self):
        """Test that alerts are NOT triggered below threshold."""
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3
        )
        
        # Only 2 failures, threshold is 3
        triggered = alert_mgr.check_and_alert(
            target_name='Test Server',
            target_type='ping',
            consecutive_failures=2
        )
        
        self.assertFalse(triggered)
        
        # Log file should be empty or not contain "ALERT"
        with open(self.log_path, 'r') as f:
            log_content = f.read()
            self.assertEqual(log_content.strip(), '')
    
    @patch('src.alerts.alert_manager.requests.post')
    def test_webhook_with_metadata(self, mock_post):
        """Test that alert metadata is included in webhook payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        alert_mgr = AlertManager(
            alert_log_path=self.log_path,
            alert_threshold=3,
            webhook_url='https://hooks.example.com/webhook/test123'
        )
        
        metadata = {
            'host': '192.168.1.10',
            'port': 22,
            'region': 'us-east-1'
        }
        
        alert_mgr.check_and_alert(
            target_name='SSH Server',
            target_type='port',
            consecutive_failures=3,
            last_error='Connection refused',
            metadata=metadata
        )
        
        # Verify metadata is in webhook payload
        payload = mock_post.call_args[1]['json']
        message = payload['content']
        self.assertIn('192.168.1.10', message)
        self.assertIn('22', message)


if __name__ == '__main__':
    unittest.main()

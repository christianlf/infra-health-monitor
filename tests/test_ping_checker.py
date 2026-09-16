"""
Unit tests for PingChecker module.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.checkers.ping_checker import PingChecker


class TestPingChecker(unittest.TestCase):
    """Test cases for PingChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = PingChecker(timeout=2)
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_successful_ping(self, mock_run):
        """Test successful ping check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.checker.check('8.8.8.8')
        
        self.assertEqual(result['status'], 'ok')
        self.assertIsNotNone(result['response_time_ms'])
        self.assertIsNone(result['error'])
        self.assertIsInstance(result['response_time_ms'], float)
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_failed_ping(self, mock_run):
        """Test failed ping check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.checker.check('192.168.255.255')
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIsNotNone(result['error'])
    
    @patch('src.checkers.ping_checker.subprocess.run')
    def test_timeout_ping(self, mock_run):
        """Test ping timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ping', 2)
        
        result = self.checker.check('192.168.1.1')
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIn('Timeout', result['error'])


if __name__ == '__main__':
    unittest.main()

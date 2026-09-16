"""
Unit tests for PortChecker module.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.checkers.port_checker import PortChecker


class TestPortChecker(unittest.TestCase):
    """Test cases for PortChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = PortChecker(timeout=2)
    
    @patch('src.checkers.port_checker.socket.socket')
    def test_successful_port_check(self, mock_socket_class):
        """Test successful port connectivity check."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_socket
        
        result = self.checker.check('localhost', 80)
        
        self.assertEqual(result['status'], 'ok')
        self.assertIsNotNone(result['response_time_ms'])
        self.assertIsNone(result['error'])
        mock_socket.close.assert_called_once()
    
    @patch('src.checkers.port_checker.socket.socket')
    def test_failed_port_check(self, mock_socket_class):
        """Test failed port connectivity check."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1
        mock_socket_class.return_value = mock_socket
        
        result = self.checker.check('localhost', 9999)
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIsNotNone(result['error'])
        mock_socket.close.assert_called_once()
    
    @patch('src.checkers.port_checker.socket.socket')
    def test_timeout_port_check(self, mock_socket_class):
        """Test port check timeout."""
        import socket
        mock_socket = MagicMock()
        mock_socket.connect_ex.side_effect = socket.timeout()
        mock_socket_class.return_value = mock_socket
        
        result = self.checker.check('10.0.0.1', 22)
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIn('timeout', result['error'].lower())
    
    @patch('src.checkers.port_checker.socket.socket')
    def test_hostname_resolution_error(self, mock_socket_class):
        """Test hostname resolution failure."""
        import socket
        mock_socket = MagicMock()
        mock_socket.connect_ex.side_effect = socket.gaierror('Name resolution failed')
        mock_socket_class.return_value = mock_socket
        
        result = self.checker.check('invalid.hostname.local', 80)
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIn('resolution', result['error'].lower())


if __name__ == '__main__':
    unittest.main()

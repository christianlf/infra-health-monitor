"""
Unit tests for HTTPChecker module.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.checkers.http_checker import HTTPChecker
import requests


class TestHTTPChecker(unittest.TestCase):
    """Test cases for HTTPChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = HTTPChecker(timeout=5)
    
    @patch('src.checkers.http_checker.requests.get')
    def test_successful_http_check(self, mock_get):
        """Test successful HTTP check with expected status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.checker.check('https://example.com', 200)
        
        self.assertEqual(result['status'], 'ok')
        self.assertIsNotNone(result['response_time_ms'])
        self.assertEqual(result['http_status'], 200)
        self.assertIsNone(result['error'])
    
    @patch('src.checkers.http_checker.requests.get')
    def test_unexpected_status_code(self, mock_get):
        """Test HTTP check with unexpected status code."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.checker.check('https://example.com/notfound', 200)
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNotNone(result['response_time_ms'])
        self.assertEqual(result['http_status'], 404)
        self.assertIn('404', result['error'])
    
    @patch('src.checkers.http_checker.requests.get')
    def test_http_timeout(self, mock_get):
        """Test HTTP request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = self.checker.check('https://slow-server.com')
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIsNone(result['http_status'])
        self.assertIn('timeout', result['error'].lower())
    
    @patch('src.checkers.http_checker.requests.get')
    def test_connection_error(self, mock_get):
        """Test HTTP connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')
        
        result = self.checker.check('https://unreachable.local')
        
        self.assertEqual(result['status'], 'fail')
        self.assertIsNone(result['response_time_ms'])
        self.assertIsNone(result['http_status'])
        self.assertIn('Connection error', result['error'])


if __name__ == '__main__':
    unittest.main()

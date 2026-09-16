"""
Unit tests for Database module.
"""

import unittest
import tempfile
import os
from src.storage.database import Database


class TestDatabase(unittest.TestCase):
    """Test cases for Database class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database and tables are created."""
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_save_check(self):
        """Test saving a check result."""
        record_id = self.db.save_check(
            target_name='Test Server',
            target_type='ping',
            status='ok',
            response_time_ms=25.5
        )
        
        self.assertIsNotNone(record_id)
        self.assertIsInstance(record_id, int)
    
    def test_get_recent_checks(self):
        """Test retrieving recent checks."""
        self.db.save_check('Server1', 'ping', 'ok', 10.5)
        self.db.save_check('Server2', 'http', 'fail', error='Timeout')
        
        recent = self.db.get_recent_checks(hours=1)
        
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]['target_name'], 'Server2')
        self.assertEqual(recent[1]['target_name'], 'Server1')
    
    def test_get_consecutive_failures(self):
        """Test counting consecutive failures."""
        target = 'Test Target'
        
        self.db.save_check(target, 'ping', 'fail')
        self.db.save_check(target, 'ping', 'fail')
        self.db.save_check(target, 'ping', 'fail')
        
        count = self.db.get_consecutive_failures(target)
        
        self.assertEqual(count, 3)
    
    def test_consecutive_failures_with_success(self):
        """Test consecutive failures reset by success."""
        target = 'Test Target'
        
        self.db.save_check(target, 'ping', 'ok', 10.0)
        self.db.save_check(target, 'ping', 'fail')
        self.db.save_check(target, 'ping', 'fail')
        
        count = self.db.get_consecutive_failures(target)
        
        self.assertEqual(count, 2)
    
    def test_get_statistics(self):
        """Test statistics calculation."""
        self.db.save_check('Server1', 'ping', 'ok', 10.0)
        self.db.save_check('Server2', 'ping', 'ok', 20.0)
        self.db.save_check('Server3', 'ping', 'fail')
        
        stats = self.db.get_statistics(hours=1)
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['success'], 2)
        self.assertEqual(stats['failure'], 1)
        self.assertAlmostEqual(stats['avg_response_time_ms'], 15.0)
        self.assertAlmostEqual(stats['success_rate'], 66.67, places=1)


if __name__ == '__main__':
    unittest.main()

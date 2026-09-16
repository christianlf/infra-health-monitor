"""
Database module - SQLite storage for health check results.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for storing health check results."""
    
    def __init__(self, db_path: str) -> None:
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_name TEXT NOT NULL,
                        target_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response_time_ms REAL,
                        error TEXT,
                        checked_at TIMESTAMP NOT NULL,
                        metadata TEXT
                    )
                """)
                
                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checked_at 
                    ON checks(checked_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_target_name 
                    ON checks(target_name)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_check(
        self,
        target_name: str,
        target_type: str,
        status: str,
        response_time_ms: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[str] = None
    ) -> int:
        """
        Save a health check result to the database.
        
        Args:
            target_name: Name of the target being checked
            target_type: Type of check (ping/port/http)
            status: Check status ('ok' or 'fail')
            response_time_ms: Response time in milliseconds
            error: Error message if check failed
            metadata: Additional metadata as JSON string
            
        Returns:
            ID of inserted record
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO checks 
                    (target_name, target_type, status, response_time_ms, error, checked_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    target_name,
                    target_type,
                    status,
                    response_time_ms,
                    error,
                    datetime.now(),
                    metadata
                ))
                conn.commit()
                record_id = cursor.lastrowid
                logger.debug(f"Saved check result for {target_name} (ID: {record_id})")
                return record_id
                
        except sqlite3.Error as e:
            logger.error(f"Error saving check result: {e}")
            raise
    
    def get_recent_checks(
        self,
        target_name: Optional[str] = None,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent check results.
        
        Args:
            target_name: Filter by specific target (optional)
            hours: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of check records as dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM checks 
                    WHERE checked_at >= datetime('now', ?)
                """
                params = [f'-{hours} hours']
                
                if target_name:
                    query += " AND target_name = ?"
                    params.append(target_name)
                
                query += " ORDER BY checked_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving check results: {e}")
            return []
    
    def get_all_checks(
        self,
        target_name: Optional[str] = None,
        limit: Optional[int] = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all check results with optional filtering.
        
        Args:
            target_name: Filter by specific target (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of check records as dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if target_name:
                    query = """
                        SELECT * FROM checks 
                        WHERE target_name = ?
                        ORDER BY checked_at DESC
                        LIMIT ?
                    """
                    cursor.execute(query, (target_name, limit))
                else:
                    query = """
                        SELECT * FROM checks 
                        ORDER BY checked_at DESC
                        LIMIT ?
                    """
                    cursor.execute(query, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all checks: {e}")
            return []
    
    def get_consecutive_failures(self, target_name: str, limit: int = 10) -> int:
        """
        Get count of consecutive failures for a target.
        
        Args:
            target_name: Name of target to check
            limit: Maximum number of recent records to examine
            
        Returns:
            Number of consecutive failures
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status FROM checks 
                    WHERE target_name = ?
                    ORDER BY checked_at DESC
                    LIMIT ?
                """, (target_name, limit))
                
                rows = cursor.fetchall()
                
                consecutive_failures = 0
                for row in rows:
                    if row['status'] == 'fail':
                        consecutive_failures += 1
                    else:
                        break
                
                return consecutive_failures
                
        except sqlite3.Error as e:
            logger.error(f"Error counting consecutive failures: {e}")
            return 0
    
    def get_statistics(self, target_name: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get statistics for checks within time period.
        
        Args:
            target_name: Filter by specific target (optional)
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with statistics (total, success, failure, avg_response_time)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                base_query = """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as success,
                        SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failure,
                        AVG(CASE WHEN status = 'ok' THEN response_time_ms ELSE NULL END) as avg_response_time
                    FROM checks
                    WHERE checked_at >= datetime('now', ?)
                """
                
                params = [f'-{hours} hours']
                
                if target_name:
                    base_query += " AND target_name = ?"
                    params.append(target_name)
                
                cursor.execute(base_query, params)
                row = cursor.fetchone()
                
                return {
                    'total': row['total'] or 0,
                    'success': row['success'] or 0,
                    'failure': row['failure'] or 0,
                    'avg_response_time_ms': round(row['avg_response_time'], 2) if row['avg_response_time'] else None,
                    'success_rate': round((row['success'] / row['total'] * 100), 2) if row['total'] > 0 else 0
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error calculating statistics: {e}")
            return {
                'total': 0,
                'success': 0,
                'failure': 0,
                'avg_response_time_ms': None,
                'success_rate': 0
            }

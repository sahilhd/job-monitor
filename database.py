import sqlite3
import json
from datetime import datetime
import threading
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path='job_monitor.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_tables()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """Initialize database tables"""
        with self.lock:
            conn = self.get_connection()
            try:
                # Monitors table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS monitors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        keywords TEXT NOT NULL,
                        selector TEXT,
                        check_interval INTEGER DEFAULT 10,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Jobs table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id INTEGER,
                        title TEXT NOT NULL,
                        url TEXT,
                        company TEXT,
                        location TEXT,
                        description TEXT,
                        content_hash TEXT UNIQUE,
                        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (monitor_id) REFERENCES monitors (id)
                    )
                ''')
                
                # Monitor runs table for statistics
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS monitor_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id INTEGER,
                        run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        jobs_found INTEGER DEFAULT 0,
                        new_jobs INTEGER DEFAULT 0,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        FOREIGN KEY (monitor_id) REFERENCES monitors (id)
                    )
                ''')
                
                conn.commit()
            finally:
                conn.close()
    
    def create_monitor(self, name: str, url: str, keywords: List[str], 
                      check_interval: int = 10, selector: str = '', 
                      is_active: bool = True) -> int:
        """Create a new monitor"""
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.execute('''
                    INSERT INTO monitors (name, url, keywords, selector, check_interval, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, url, json.dumps(keywords), selector, check_interval, is_active))
                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()
    
    def get_monitor(self, monitor_id: int) -> Optional[Dict]:
        """Get a monitor by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM monitors WHERE id = ?', (monitor_id,))
            row = cursor.fetchone()
            if row:
                monitor = dict(row)
                monitor['keywords'] = json.loads(monitor['keywords'])
                return monitor
            return None
        finally:
            conn.close()
    
    def get_all_monitors(self) -> List[Dict]:
        """Get all monitors"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM monitors ORDER BY created_at DESC')
            monitors = []
            for row in cursor.fetchall():
                monitor = dict(row)
                monitor['keywords'] = json.loads(monitor['keywords'])
                monitors.append(monitor)
            return monitors
        finally:
            conn.close()
    
    def update_monitor(self, monitor_id: int, **kwargs) -> bool:
        """Update a monitor"""
        with self.lock:
            conn = self.get_connection()
            try:
                # Build update query dynamically
                updates = []
                values = []
                
                for key, value in kwargs.items():
                    if key == 'keywords' and isinstance(value, list):
                        value = json.dumps(value)
                    updates.append(f"{key} = ?")
                    values.append(value)
                
                if not updates:
                    return False
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(monitor_id)
                
                query = f"UPDATE monitors SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, values)
                conn.commit()
                return conn.changes > 0
            finally:
                conn.close()
    
    def delete_monitor(self, monitor_id: int) -> bool:
        """Delete a monitor and its associated data"""
        with self.lock:
            conn = self.get_connection()
            try:
                # Delete associated jobs and runs
                conn.execute('DELETE FROM jobs WHERE monitor_id = ?', (monitor_id,))
                conn.execute('DELETE FROM monitor_runs WHERE monitor_id = ?', (monitor_id,))
                conn.execute('DELETE FROM monitors WHERE id = ?', (monitor_id,))
                conn.commit()
                return conn.changes > 0
            finally:
                conn.close()
    
    def get_active_monitors(self) -> List[Dict]:
        """Get all active monitors"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM monitors WHERE is_active = 1')
            monitors = []
            for row in cursor.fetchall():
                monitor = dict(row)
                monitor['keywords'] = json.loads(monitor['keywords'])
                monitors.append(monitor)
            return monitors
        finally:
            conn.close()
    
    def save_job(self, monitor_id: int, title: str, url: str = None, 
                company: str = None, location: str = None, 
                description: str = None, content_hash: str = None) -> Optional[int]:
        """Save a job posting"""
        with self.lock:
            conn = self.get_connection()
            try:
                cursor = conn.execute('''
                    INSERT OR IGNORE INTO jobs 
                    (monitor_id, title, url, company, location, description, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (monitor_id, title, url, company, location, description, content_hash))
                conn.commit()
                return cursor.lastrowid if cursor.rowcount > 0 else None
            finally:
                conn.close()
    
    def get_jobs(self, monitor_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get job postings"""
        conn = self.get_connection()
        try:
            if monitor_id:
                cursor = conn.execute('''
                    SELECT j.*, m.name as monitor_name 
                    FROM jobs j 
                    JOIN monitors m ON j.monitor_id = m.id 
                    WHERE j.monitor_id = ? 
                    ORDER BY j.detected_at DESC 
                    LIMIT ?
                ''', (monitor_id, limit))
            else:
                cursor = conn.execute('''
                    SELECT j.*, m.name as monitor_name 
                    FROM jobs j 
                    JOIN monitors m ON j.monitor_id = m.id 
                    ORDER BY j.detected_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def record_monitor_run(self, monitor_id: int, jobs_found: int, 
                          new_jobs: int, success: bool = True, 
                          error_message: str = None):
        """Record a monitor run for statistics"""
        with self.lock:
            conn = self.get_connection()
            try:
                conn.execute('''
                    INSERT INTO monitor_runs 
                    (monitor_id, jobs_found, new_jobs, success, error_message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (monitor_id, jobs_found, new_jobs, success, error_message))
                conn.commit()
            finally:
                conn.close()
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        conn = self.get_connection()
        try:
            # Total monitors
            total_monitors = conn.execute('SELECT COUNT(*) FROM monitors').fetchone()[0]
            active_monitors = conn.execute('SELECT COUNT(*) FROM monitors WHERE is_active = 1').fetchone()[0]
            
            # Total jobs
            total_jobs = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
            
            # Jobs found today
            jobs_today = conn.execute('''
                SELECT COUNT(*) FROM jobs 
                WHERE DATE(detected_at) = DATE('now')
            ''').fetchone()[0]
            
            # Recent runs
            recent_runs = conn.execute('''
                SELECT mr.*, m.name as monitor_name
                FROM monitor_runs mr
                JOIN monitors m ON mr.monitor_id = m.id
                ORDER BY mr.run_at DESC
                LIMIT 10
            ''').fetchall()
            
            return {
                'total_monitors': total_monitors,
                'active_monitors': active_monitors,
                'total_jobs': total_jobs,
                'jobs_today': jobs_today,
                'recent_runs': [dict(row) for row in recent_runs]
            }
        finally:
            conn.close()
    
    def job_exists(self, content_hash: str) -> bool:
        """Check if a job with the given content hash already exists"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT 1 FROM jobs WHERE content_hash = ?', (content_hash,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

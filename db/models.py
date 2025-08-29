#!/usr/bin/env python3
"""
Database Models for Nutrient Mixing System
SQLite models for tank state management, job tracking, and logging
"""

import sqlite3
import logging
import threading
import time
from queue import Queue, Empty
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)

# Global database manager instance (singleton)
_global_db_manager = None
_db_lock = threading.Lock()

class TankState(Enum):
    """Tank state enumeration"""
    IDLE = "idle"
    FILLING = "filling"
    MIXING = "mixing"
    SENDING = "sending"

class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    """Job type enumeration"""
    FILL = "fill"
    MIX = "mix"
    SEND = "send"

class DatabaseConnectionPool:
    """Thread-safe database connection pool with proper resource management"""
    
    def __init__(self, db_path: str = "database.db", max_connections: int = 20):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        self._closed = False
        
        # Pre-create initial connections
        self._initialize_pool()
        logger.info(f"Database pool initialized with {self._created_connections}/{max_connections} connections")
    
    def _initialize_pool(self):
        """Initialize the connection pool with starting connections"""
        initial_connections = min(5, self.max_connections)
        for _ in range(initial_connections):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
                self._created_connections += 1
    
    def _create_connection(self):
        """Create a new database connection with proper settings"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0  # 30 second timeout
            )
            conn.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")  # 10 second busy timeout
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
            
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    def get_connection(self, timeout=10.0):
        """Get a connection from the pool"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        # Try to get existing connection from pool
        try:
            conn = self._pool.get(timeout=timeout)
            # Test if connection is still valid
            try:
                conn.execute("SELECT 1").fetchone()
                return conn
            except sqlite3.Error:
                # Connection is bad, close it and create new one
                conn.close()
                with self._lock:
                    self._created_connections -= 1
                # Fall through to create new connection
        except Empty:
            pass  # Pool is empty, create new connection
        
        # Create new connection if under limit
        with self._lock:
            if self._created_connections < self.max_connections:
                conn = self._create_connection()
                if conn:
                    self._created_connections += 1
                    return conn
        
        # Pool is full and at max connections
        logger.warning(f"Database pool at maximum capacity ({self.max_connections}), waiting for available connection...")
        try:
            conn = self._pool.get(timeout=timeout)
            conn.execute("SELECT 1").fetchone()  # Validate connection
            return conn
        except (Empty, sqlite3.Error) as e:
            logger.error(f"Failed to get database connection: {e}")
            return None
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if not conn or self._closed:
            if conn:
                conn.close()
            return
        
        try:
            # Test if connection is still good
            conn.execute("SELECT 1").fetchone()
            
            # Try to put back in pool (non-blocking)
            try:
                self._pool.put_nowait(conn)
            except:
                # Pool is full, close the excess connection
                conn.close()
                with self._lock:
                    self._created_connections -= 1
                    
        except sqlite3.Error:
            # Connection is bad, close it
            conn.close()
            with self._lock:
                self._created_connections -= 1
    
    @contextmanager
    def get_connection_context(self):
        """Context manager for automatic connection management"""
        conn = self.get_connection()
        if not conn:
            raise RuntimeError("Could not obtain database connection")
        
        try:
            yield conn
        except Exception:
            # Rollback on exception
            try:
                conn.rollback()
            except:
                pass
            raise
        finally:
            self.return_connection(conn)
    
    def close_all(self):
        """Close all connections in the pool"""
        self._closed = True
        
        # Close all pooled connections
        while True:
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        with self._lock:
            self._created_connections = 0
        
        logger.info("Database connection pool closed")


class DatabaseManager:
    """Improved Database manager using singleton pattern and connection pooling"""
    
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path, max_connections=20)
        self.init_database()
    
    def get_connection(self):
        """Get database connection context manager"""
        return self.pool.get_connection_context()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            # Tank table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tanks (
                    tank_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    capacity_gallons REAL NOT NULL,
                    current_volume REAL DEFAULT 0.0,
                    state TEXT DEFAULT 'idle',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Job table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT NOT NULL,
                    tank_id INTEGER NOT NULL,
                    parameters TEXT,
                    status TEXT DEFAULT 'pending',
                    progress REAL DEFAULT 0.0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (tank_id) REFERENCES tanks (tank_id)
                )
            """)
            
            # Sensor log table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sensor_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tank_id INTEGER,
                    ph_reading REAL,
                    ec_reading REAL,
                    temperature REAL,
                    FOREIGN KEY (tank_id) REFERENCES tanks (tank_id)
                )
            """)
            
            # Hardware log table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hardware_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    component TEXT NOT NULL,
                    component_id INTEGER,
                    action TEXT NOT NULL,
                    result TEXT,
                    error_message TEXT
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_tank_id ON jobs(tank_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sensor_logs_timestamp ON sensor_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hardware_logs_timestamp ON hardware_logs(timestamp)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def close(self):
        """Close the database manager and all connections"""
        self.pool.close_all()

class Tank:
    """Tank model"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, tank_id: int, name: str, capacity_gallons: float) -> bool:
        """Create a new tank"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tanks (tank_id, name, capacity_gallons, current_volume, state)
                    VALUES (?, ?, ?, 0.0, ?)
                """, (tank_id, name, capacity_gallons, TankState.IDLE.value))
                conn.commit()
                logger.info(f"Tank {tank_id} created: {name} ({capacity_gallons} gal)")
                return True
        except Exception as e:
            logger.error(f"Failed to create tank {tank_id}: {e}")
            return False
    
    def get(self, tank_id: int) -> Optional[Dict[str, Any]]:
        """Get tank by ID"""
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM tanks WHERE tank_id = ?", (tank_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get tank {tank_id}: {e}")
            return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all tanks"""
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute("SELECT * FROM tanks ORDER BY tank_id").fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get all tanks: {e}")
            return []
    
    def update_state(self, tank_id: int, state: TankState) -> bool:
        """Update tank state"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE tanks 
                    SET state = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE tank_id = ?
                """, (state.value, tank_id))
                conn.commit()
                logger.debug(f"Tank {tank_id} state updated to {state.value}")
                return True
        except Exception as e:
            logger.error(f"Failed to update tank {tank_id} state: {e}")
            return False
    
    def update_volume(self, tank_id: int, volume: float) -> bool:
        """Update tank current volume"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE tanks 
                    SET current_volume = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE tank_id = ?
                """, (volume, tank_id))
                conn.commit()
                logger.debug(f"Tank {tank_id} volume updated to {volume} gallons")
                return True
        except Exception as e:
            logger.error(f"Failed to update tank {tank_id} volume: {e}")
            return False
    
    def is_available(self, tank_id: int) -> bool:
        """Check if tank is available for new operations"""
        tank = self.get(tank_id)
        if not tank:
            return False
        return tank['state'] == TankState.IDLE.value

class Job:
    """Job model"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, job_type: JobType, tank_id: int, parameters: Dict[str, Any] = None) -> Optional[int]:
        """Create a new job"""
        try:
            params_json = json.dumps(parameters) if parameters else None
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO jobs (job_type, tank_id, parameters, status)
                    VALUES (?, ?, ?, ?)
                """, (job_type.value, tank_id, params_json, JobStatus.PENDING.value))
                job_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Job {job_id} created: {job_type.value} for tank {tank_id}")
                return job_id
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            return None
    
    def get(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
                ).fetchone()
                if row:
                    job = dict(row)
                    if job['parameters']:
                        job['parameters'] = json.loads(job['parameters'])
                    return job
                return None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """Get all pending jobs"""
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE status = ? 
                    ORDER BY created_at
                """, (JobStatus.PENDING.value,)).fetchall()
                
                jobs = []
                for row in rows:
                    job = dict(row)
                    if job['parameters']:
                        job['parameters'] = json.loads(job['parameters'])
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Failed to get pending jobs: {e}")
            return []
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all running jobs"""
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE status = ? 
                    ORDER BY started_at
                """, (JobStatus.RUNNING.value,)).fetchall()
                
                jobs = []
                for row in rows:
                    job = dict(row)
                    if job['parameters']:
                        job['parameters'] = json.loads(job['parameters'])
                    jobs.append(job)
                return jobs
        except Exception as e:
            logger.error(f"Failed to get active jobs: {e}")
            return []
    
    def update_status(self, job_id: int, status: JobStatus, progress: float = None, 
                     error_message: str = None) -> bool:
        """Update job status"""
        try:
            with self.db.get_connection() as conn:
                if status == JobStatus.RUNNING:
                    conn.execute("""
                        UPDATE jobs 
                        SET status = ?, started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE job_id = ?
                    """, (status.value, job_id))
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    conn.execute("""
                        UPDATE jobs 
                        SET status = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP,
                            progress = ?, error_message = ?
                        WHERE job_id = ?
                    """, (status.value, progress or 100.0, error_message, job_id))
                else:
                    conn.execute("""
                        UPDATE jobs 
                        SET status = ?, updated_at = CURRENT_TIMESTAMP, progress = ?, error_message = ?
                        WHERE job_id = ?
                    """, (status.value, progress, error_message, job_id))
                
                conn.commit()
                logger.debug(f"Job {job_id} status updated to {status.value}")
                return True
        except Exception as e:
            logger.error(f"Failed to update job {job_id} status: {e}")
            return False
    
    def update_progress(self, job_id: int, progress: float) -> bool:
        """Update job progress"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE jobs 
                    SET progress = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE job_id = ?
                """, (progress, job_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update job {job_id} progress: {e}")
            return False

class SensorLog:
    """Sensor log model"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_reading(self, tank_id: int = None, ph_reading: float = None, 
                   ec_reading: float = None, temperature: float = None) -> bool:
        """Add sensor reading"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO sensor_logs (tank_id, ph_reading, ec_reading, temperature)
                    VALUES (?, ?, ?, ?)
                """, (tank_id, ph_reading, ec_reading, temperature))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add sensor reading: {e}")
            return False
    
    def get_latest_readings(self, tank_id: int = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest sensor readings"""
        try:
            with self.db.get_connection() as conn:
                if tank_id:
                    rows = conn.execute("""
                        SELECT * FROM sensor_logs 
                        WHERE tank_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (tank_id, limit)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT * FROM sensor_logs 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get sensor readings: {e}")
            return []

class HardwareLog:
    """Hardware log model"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def log_action(self, component: str, component_id: int, action: str, 
                  result: str = None, error_message: str = None) -> bool:
        """Log hardware action"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO hardware_logs (component, component_id, action, result, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (component, component_id, action, result, error_message))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to log hardware action: {e}")
            return False
    
    def get_recent_logs(self, component: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent hardware logs"""
        try:
            with self.db.get_connection() as conn:
                if component:
                    rows = conn.execute("""
                        SELECT * FROM hardware_logs 
                        WHERE component = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (component, limit)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT * FROM hardware_logs 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get hardware logs: {e}")
            return []

def get_database_manager(db_path: str = "database.db") -> DatabaseManager:
    """Get the global database manager instance (singleton pattern)"""
    global _global_db_manager
    
    if _global_db_manager is None:
        with _db_lock:
            if _global_db_manager is None:
                _global_db_manager = DatabaseManager(db_path)
                logger.info("Global database manager created")
    
    return _global_db_manager


# Initialize database and models
def init_models(db_path: str = "database.db"):
    """Initialize database models using singleton database manager"""
    # Use singleton database manager instead of creating new instance
    db_manager = get_database_manager(db_path)
    
    # Initialize tanks from config
    from config import TANKS
    tank_model = Tank(db_manager)
    
    for tank_id, tank_config in TANKS.items():
        tank_model.create(
            tank_id=tank_id,
            name=tank_config['name'],
            capacity_gallons=tank_config['capacity_gallons']
        )
    
    return {
        'db_manager': db_manager,
        'tank': tank_model,
        'job': Job(db_manager),
        'sensor_log': SensorLog(db_manager),
        'hardware_log': HardwareLog(db_manager)
    }

if __name__ == "__main__":
    # Test the models
    logging.basicConfig(level=logging.INFO)
    models = init_models("test_database.db")
    
    print("Database models test:")
    print("- Tanks:", len(models['tank'].get_all()))
    
    # Test job creation
    job_id = models['job'].create(JobType.FILL, 1, {"gallons": 50})
    if job_id:
        print(f"- Created test job: {job_id}")
        job = models['job'].get(job_id)
        print(f"- Job details: {job}")
    
    # Test sensor log
    models['sensor_log'].add_reading(tank_id=1, ph_reading=6.5, ec_reading=1.2)
    readings = models['sensor_log'].get_latest_readings(limit=1)
    print(f"- Latest sensor reading: {readings}")
    
    # Test hardware log
    models['hardware_log'].log_action("relay", 1, "turn_on", "success")
    logs = models['hardware_log'].get_recent_logs(limit=1)
    print(f"- Latest hardware log: {logs}")
    
    print("Models test completed successfully!")
#!/usr/bin/env python3
"""
Database Models for Nutrient Mixing System
SQLite models for tank state management, job tracking, and logging
"""

import sqlite3
import logging
import queue
import threading
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)

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

class DatabasePool:
    """Database connection pool for improved performance"""
    
    def __init__(self, db_path: str = "database.db", max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        
        # Initialize connection pool
        for _ in range(max_connections):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.pool.put(conn)
        
        logger.info(f"Database pool initialized with {max_connections} connections")
    
    def get_connection(self):
        """Get connection from pool"""
        try:
            return self.pool.get(timeout=5.0)
        except queue.Empty:
            logger.warning("Database pool exhausted, creating temporary connection")
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
    
    def return_connection(self, conn):
        """Return connection to pool"""
        try:
            self.pool.put_nowait(conn)
        except queue.Full:
            # Pool is full, close the connection
            conn.close()
    
    def close_all(self):
        """Close all connections in pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break
        logger.info("Database pool closed")

class DatabaseManager:
    """Database manager for SQLite operations with connection pooling"""
    
    def __init__(self, db_path: str = "database.db", use_pool: bool = True):
        self.db_path = db_path
        self.use_pool = use_pool
        
        if use_pool:
            self.pool = DatabasePool(db_path)
        else:
            self.pool = None
        
        self.init_database()
    
    def get_connection(self):
        """Get database connection (pooled or direct)"""
        if self.pool:
            return self.pool.get_connection()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
    
    def return_connection(self, conn):
        """Return connection to pool or close if not using pool"""
        if self.pool:
            self.pool.return_connection(conn)
        else:
            conn.close()
    
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
                    parameters TEXT,  -- JSON string
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
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_tank_id ON jobs(tank_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sensor_logs_timestamp ON sensor_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hardware_logs_timestamp ON hardware_logs(timestamp)")
            
            conn.commit()
            logger.info("Database initialized successfully")

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

# Initialize database and models
def init_models(db_path: str = "database.db"):
    """Initialize database models"""
    db_manager = DatabaseManager(db_path)
    
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
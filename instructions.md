# Database Connection Pool Fix - Implementation Guide

## Problem Analysis
The Flask application is experiencing database connection pool exhaustion with these symptoms:
- Repeated "Database pool initialized with 5 connections" log messages
- Continuous "Database pool exhausted, creating temporary connection" warnings
- Multiple DatabaseManager instances being created instead of reusing one

## Root Causes
1. **Multiple Database Manager Instances**: Each component creates its own DatabaseManager
2. **Small Pool Size**: Only 5 connections for a multi-threaded Flask app with real-time updates
3. **No Singleton Pattern**: Multiple pools competing for same database
4. **Connection Leaks**: Connections not properly returned to pool

## Complete Fix Implementation

### 1. Replace DatabaseManager Class in `models.py`

```python
import sqlite3
import logging
import threading
import time
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# Global database manager instance (singleton)
_global_db_manager = None
_db_lock = threading.Lock()

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


def get_database_manager(db_path: str = "database.db") -> DatabaseManager:
    """Get the global database manager instance (singleton pattern)"""
    global _global_db_manager
    
    if _global_db_manager is None:
        with _db_lock:
            if _global_db_manager is None:
                _global_db_manager = DatabaseManager(db_path)
                logger.info("Global database manager created")
    
    return _global_db_manager
```

### 2. Update init_models Function

```python
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
```

### 3. Update Flask App Initialization

In your `app.py` file, modify the initialization:

```python
# At the top of app.py, replace database initialization
from models import get_database_manager, init_models

# Initialize models ONCE at startup
logger.info("🔧 Initializing database models...")
models = init_models()
db_manager = models['db_manager']
logger.info("✅ Database models initialized")

# Use the same models throughout the app
tank_model = models['tank']
job_model = models['job']
sensor_log_model = models['sensor_log']
hardware_log_model = models['hardware_log']
```

### 4. Update Hardware Manager Initialization

In `hardware_manager.py`, use the singleton database manager:

```python
from models import get_database_manager, HardwareLog

class HardwareManager:
    def __init__(self, use_mock_hardware: bool = None):
        # Use singleton database manager instead of creating new one
        self.db_manager = get_database_manager()
        self.hardware_log = HardwareLog(self.db_manager)
        
        # ... rest of initialization
```

### 5. Update Scheduler Initialization

In `scheduler.py`, use the singleton database manager:

```python
from models import get_database_manager, Tank, Job

class JobScheduler:
    def __init__(self, hardware_manager: HardwareManager, db_path: str = "database.db"):
        self.hardware = hardware_manager
        
        # Use singleton database manager
        self.db_manager = get_database_manager(db_path)
        self.tank_model = Tank(self.db_manager)
        self.job_model = Job(self.db_manager)
        
        # ... rest of initialization
```

## Key Benefits of This Fix

1. **Singleton Pattern**: Only one database manager instance across entire application
2. **Larger Pool Size**: 20 connections instead of 5
3. **Proper Connection Management**: Automatic return to pool with context managers
4. **Connection Validation**: Tests connections before reuse
5. **Graceful Degradation**: Handles pool exhaustion better
6. **Performance Improvements**: WAL mode, proper timeouts, connection reuse
7. **Thread Safety**: Proper locking and thread-safe operations

## Expected Results After Fix

- ✅ No more "Database pool exhausted" warnings
- ✅ Single "Database pool initialized" message at startup
- ✅ Better performance with connection reuse
- ✅ More stable database operations under load
- ✅ Proper resource cleanup on shutdown

## Implementation Steps

1. **Backup current models.py**
2. **Replace DatabaseManager class** with the improved version above
3. **Add the singleton pattern functions**
4. **Update all imports** to use `get_database_manager()`
5. **Update app.py, hardware_manager.py, scheduler.py** to use singleton
6. **Test the application** - should see only one pool initialization message
7. **Monitor logs** - no more pool exhaustion warnings

## Testing the Fix

After implementation, you should see in the logs:
```
INFO:models:Database pool initialized with 5/20 connections
INFO:models:Global database manager created
INFO:models:Database initialized successfully
```

And NO MORE repeated pool initialization or exhaustion warnings.
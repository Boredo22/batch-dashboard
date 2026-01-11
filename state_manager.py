"""
Local State Manager for Hardware State Persistence

HIGH-PERFORMANCE VERSION with:
- In-memory cache for instant hardware state access (no I/O)
- Async background persistence to SQLite (never blocks hardware ops)
- Connection pooling (no per-operation connection overhead)
- WAL mode for better concurrent access

Usage:
    from state_manager import state

    # Simple key-value (instant - uses cache)
    state.set("relay_1", "on")
    current = state.get("relay_1", default="off")

    # Bulk operations
    state.set_many({"relay_1": "on", "relay_2": "off", "tank_1": "filling"})
    all_relays = state.get_prefix("relay_")
"""

import sqlite3
import threading
import json
import queue
import atexit
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

# Database location - in the project root, survives restarts
DEFAULT_DB_PATH = Path(__file__).parent / "hardware_state.db"


class ConnectionPool:
    """Thread-safe SQLite connection pool with WAL mode."""

    def __init__(self, db_path: str, size: int = 3):
        self.db_path = db_path
        self.size = size
        self._pool = queue.Queue(maxsize=size)
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self):
        """Create the connection pool. Call once at startup."""
        with self._lock:
            if self._initialized:
                return
            for _ in range(self.size):
                conn = self._create_connection()
                self._pool.put(conn)
            self._initialized = True

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new optimized SQLite connection."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode
        )
        conn.row_factory = sqlite3.Row
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=5000")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            self.initialize()

        conn = self._pool.get(timeout=30.0)
        try:
            yield conn
        finally:
            self._pool.put(conn)

    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            self._initialized = False


class HardwareStateCache:
    """
    Thread-safe in-memory cache for real-time hardware state.

    This is the hot path - all reads and writes are instant.
    Changes are queued for async persistence to SQLite.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._data: Dict[str, Any] = {}
        self._dirty_keys: set = set()  # Keys that need persistence

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache (instant)."""
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in cache and mark for persistence."""
        with self._lock:
            self._data[key] = value
            self._dirty_keys.add(key)

    def delete(self, key: str) -> None:
        """Delete a key from cache."""
        with self._lock:
            self._data.pop(key, None)
            self._dirty_keys.discard(key)

    def get_prefix(self, prefix: str) -> Dict[str, Any]:
        """Get all keys starting with prefix."""
        with self._lock:
            return {k: v for k, v in self._data.items() if k.startswith(prefix)}

    def get_all(self) -> Dict[str, Any]:
        """Get all cached data."""
        with self._lock:
            return dict(self._data)

    def set_many(self, items: Dict[str, Any]) -> None:
        """Set multiple values at once."""
        with self._lock:
            self._data.update(items)
            self._dirty_keys.update(items.keys())

    def clear_prefix(self, prefix: str) -> None:
        """Delete all keys with prefix."""
        with self._lock:
            keys_to_remove = [k for k in self._data if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._data[k]
                self._dirty_keys.discard(k)

    def get_dirty_keys(self) -> Dict[str, Any]:
        """Get all dirty (modified) key-value pairs and clear dirty set."""
        with self._lock:
            dirty_data = {k: self._data[k] for k in self._dirty_keys if k in self._data}
            self._dirty_keys.clear()
            return dirty_data

    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load data from dict (used at startup)."""
        with self._lock:
            self._data.update(data)
            # Don't mark as dirty - this is initial load


class AsyncPersistenceWriter:
    """
    Background thread that persists cache changes to SQLite.

    Batches writes for efficiency - flushes every 100ms or when batch is full.
    Never blocks the main thread.
    """

    def __init__(self, pool: ConnectionPool, cache: HardwareStateCache):
        self._pool = pool
        self._cache = cache
        self._write_queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._flush_interval = 0.1  # 100ms
        self._batch_size = 20

    def start(self):
        """Start the background persistence thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the persistence thread and flush pending writes."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self._flush_now()

    def queue_write(self, key: str, value: Any):
        """Queue a key-value pair for persistence."""
        self._write_queue.put((key, value))

    def queue_delete(self, key: str):
        """Queue a key for deletion."""
        self._write_queue.put((key, None))  # None value = delete

    def _writer_loop(self):
        """Main loop for the persistence thread."""
        while self._running:
            try:
                # Collect batch from queue
                batch = []
                try:
                    # Wait for first item with timeout
                    item = self._write_queue.get(timeout=self._flush_interval)
                    batch.append(item)

                    # Collect more items without blocking
                    while len(batch) < self._batch_size:
                        try:
                            item = self._write_queue.get_nowait()
                            batch.append(item)
                        except queue.Empty:
                            break
                except queue.Empty:
                    pass

                # Also get any dirty keys from cache
                dirty = self._cache.get_dirty_keys()
                for k, v in dirty.items():
                    batch.append((k, v))

                # Flush batch to database
                if batch:
                    self._flush_batch(batch)

            except Exception as e:
                print(f"[AsyncPersistenceWriter] Error in writer loop: {e}")

    def _flush_batch(self, batch: List[tuple]):
        """Write a batch of key-value pairs to SQLite."""
        if not batch:
            return

        try:
            with self._pool.get_connection() as conn:
                now = datetime.now().isoformat()

                # Separate writes and deletes
                writes = [(k, v, now) for k, v in batch if v is not None]
                deletes = [k for k, v in batch if v is None]

                if writes:
                    # Batch insert/update
                    conn.execute("BEGIN")
                    try:
                        for key, value, ts in writes:
                            if not isinstance(value, str):
                                value = json.dumps(value)
                            conn.execute('''
                                INSERT OR REPLACE INTO state (key, value, updated_at)
                                VALUES (?, ?, ?)
                            ''', (key, value, ts))
                        conn.execute("COMMIT")
                    except Exception:
                        conn.execute("ROLLBACK")
                        raise

                if deletes:
                    conn.execute("BEGIN")
                    try:
                        for key in deletes:
                            conn.execute("DELETE FROM state WHERE key = ?", (key,))
                        conn.execute("COMMIT")
                    except Exception:
                        conn.execute("ROLLBACK")
                        raise

        except Exception as e:
            print(f"[AsyncPersistenceWriter] Error flushing batch: {e}")

    def _flush_now(self):
        """Immediately flush any pending writes (called on shutdown)."""
        # Drain queue
        batch = []
        while not self._write_queue.empty():
            try:
                batch.append(self._write_queue.get_nowait())
            except queue.Empty:
                break

        # Get remaining dirty keys
        dirty = self._cache.get_dirty_keys()
        for k, v in dirty.items():
            batch.append((k, v))

        self._flush_batch(batch)


class StateManager:
    """
    High-performance state manager with in-memory cache and async persistence.

    All hardware state reads/writes are instant (from cache).
    Changes are persisted to SQLite in the background.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DEFAULT_DB_PATH)
        self._lock = threading.RLock()

        # Initialize components
        self._pool = ConnectionPool(self.db_path)
        self._cache = HardwareStateCache()
        self._writer = AsyncPersistenceWriter(self._pool, self._cache)

        # Initialize database and load cache
        self._init_db()
        self._load_cache_from_db()

        # Start background persistence
        self._writer.start()

        # Ensure clean shutdown
        atexit.register(self._shutdown)

    def _shutdown(self):
        """Clean shutdown - flush pending writes."""
        self._writer.stop()
        self._pool.close_all()

    def _init_db(self):
        """Initialize the database schema with WAL mode."""
        self._pool.initialize()

        with self._pool.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_state_updated
                ON state(updated_at);

                CREATE TABLE IF NOT EXISTS job_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tank_id INTEGER,
                    room_id TEXT,
                    target_value REAL,
                    actual_value REAL,
                    parameters TEXT,
                    error_message TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_job_history_type
                ON job_history(job_type);

                CREATE INDEX IF NOT EXISTS idx_job_history_status
                ON job_history(status);

                CREATE INDEX IF NOT EXISTS idx_job_history_started
                ON job_history(started_at DESC);
            ''')

    def _load_cache_from_db(self):
        """Load all state from SQLite into cache at startup."""
        try:
            with self._pool.get_connection() as conn:
                rows = conn.execute("SELECT key, value FROM state").fetchall()
                data = {}
                for row in rows:
                    value = row['value']
                    try:
                        value = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    data[row['key']] = value
                self._cache.load_from_dict(data)
                print(f"[StateManager] Loaded {len(data)} state entries from database")
        except Exception as e:
            print(f"[StateManager] Error loading cache from DB: {e}")

    # =========================================================================
    # LEGACY CONTEXT MANAGER (for backwards compatibility with job history)
    # =========================================================================

    @contextmanager
    def _get_conn(self):
        """Get a database connection (for job history operations)."""
        with self._pool.get_connection() as conn:
            yield conn

    # =========================================================================
    # CORE OPERATIONS - All use cache for instant access
    # =========================================================================

    def set(self, key: str, value: Any) -> bool:
        """
        Set a state value. Instant (cache) with async persistence.

        Args:
            key: State key (e.g., "relay_1", "tank_1_state")
            value: Any JSON-serializable value

        Returns:
            True if successful
        """
        try:
            self._cache.set(key, value)
            return True
        except Exception as e:
            print(f"[StateManager] Error setting {key}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a state value. Instant (from cache).

        Args:
            key: State key
            default: Value to return if key doesn't exist

        Returns:
            The stored value, or default if not found
        """
        return self._cache.get(key, default)

    def delete(self, key: str) -> bool:
        """Delete a state key."""
        try:
            self._cache.delete(key)
            self._writer.queue_delete(key)
            return True
        except Exception as e:
            print(f"[StateManager] Error deleting {key}: {e}")
            return False

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def set_many(self, items: Dict[str, Any]) -> bool:
        """
        Set multiple state values atomically.

        Args:
            items: Dict of key-value pairs

        Returns:
            True if all successful
        """
        try:
            self._cache.set_many(items)
            return True
        except Exception as e:
            print(f"[StateManager] Error in set_many: {e}")
            return False

    def get_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        Get all state keys starting with a prefix.

        Args:
            prefix: Key prefix (e.g., "relay_" gets relay_1, relay_2, etc.)

        Returns:
            Dict of matching key-value pairs
        """
        return self._cache.get_prefix(prefix)

    def get_all(self) -> Dict[str, Any]:
        """Get all stored state."""
        return self._cache.get_all()

    def clear_prefix(self, prefix: str) -> bool:
        """Delete all keys with a given prefix."""
        try:
            # Get keys before clearing for async delete
            keys = list(self._cache.get_prefix(prefix).keys())
            self._cache.clear_prefix(prefix)
            for key in keys:
                self._writer.queue_delete(key)
            return True
        except Exception as e:
            print(f"[StateManager] Error in clear_prefix: {e}")
            return False

    # =========================================================================
    # CONVENIENCE METHODS FOR HARDWARE
    # =========================================================================

    def set_relay(self, relay_id: int, is_on: bool) -> bool:
        """Set relay state."""
        return self.set(f"relay_{relay_id}", "on" if is_on else "off")

    def get_relay(self, relay_id: int) -> bool:
        """Get relay state. Returns False if unknown."""
        return self.get(f"relay_{relay_id}", "off") == "on"

    def get_all_relays(self) -> Dict[int, bool]:
        """Get all relay states as {relay_id: is_on}."""
        raw = self.get_prefix("relay_")
        return {
            int(k.replace("relay_", "")): (v == "on")
            for k, v in raw.items()
            if k.replace("relay_", "").isdigit()
        }

    def set_tank_state(self, tank_id: int, state: str) -> bool:
        """Set tank state (idle, filling, mixing, sending, error)."""
        return self.set(f"tank_{tank_id}_state", state)

    def get_tank_state(self, tank_id: int) -> str:
        """Get tank state. Returns 'idle' if unknown."""
        return self.get(f"tank_{tank_id}_state", "idle")

    def set_process(self, process_id: str, data: Dict[str, Any]) -> bool:
        """Store process data (progress, status, etc.)."""
        return self.set(f"process_{process_id}", data)

    def get_process(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get process data."""
        return self.get(f"process_{process_id}")

    def get_active_processes(self) -> Dict[str, Dict[str, Any]]:
        """Get all process data."""
        raw = self.get_prefix("process_")
        return {
            k.replace("process_", ""): v
            for k, v in raw.items()
        }

    # =========================================================================
    # PUMP STATE TRACKING
    # =========================================================================

    def set_pump_state(self, pump_id: int, is_active: bool) -> bool:
        """Set pump active state (dispensing or not)."""
        return self.set(f"pump_{pump_id}_active", is_active)

    def get_pump_state(self, pump_id: int) -> bool:
        """Get pump active state. Returns False if unknown."""
        return self.get(f"pump_{pump_id}_active", False)

    def set_pump_job(self, pump_id: int, job_data: Dict[str, Any]) -> bool:
        """
        Set current pump job data.

        Args:
            pump_id: Pump ID
            job_data: Dict with keys:
                - total_ml: Total volume for this job
                - ml_dispensed: Volume dispensed so far
                - job_id: Optional job identifier
                - started_at: ISO timestamp when job started
        """
        return self.set(f"pump_{pump_id}_job", job_data)

    def get_pump_job(self, pump_id: int) -> Optional[Dict[str, Any]]:
        """Get current pump job data."""
        return self.get(f"pump_{pump_id}_job")

    def clear_pump_job(self, pump_id: int) -> bool:
        """Clear pump job data (call when job completes)."""
        return self.delete(f"pump_{pump_id}_job")

    def set_pump_calibration_date(self, pump_id: int, date_iso: str) -> bool:
        """Set pump last calibration date (ISO format)."""
        return self.set(f"pump_{pump_id}_calibration_date", date_iso)

    def get_pump_calibration_date(self, pump_id: int) -> Optional[str]:
        """Get pump last calibration date."""
        return self.get(f"pump_{pump_id}_calibration_date")

    def get_all_pumps(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all pump states as {pump_id: {active, job, calibration_date}}.
        """
        pumps = {}
        raw = self.get_prefix("pump_")

        # Group by pump_id
        for key, value in raw.items():
            if "_active" in key:
                pump_id = int(key.replace("pump_", "").replace("_active", ""))
                if pump_id not in pumps:
                    pumps[pump_id] = {}
                pumps[pump_id]["active"] = value
            elif "_job" in key:
                pump_id = int(key.replace("pump_", "").replace("_job", ""))
                if pump_id not in pumps:
                    pumps[pump_id] = {}
                pumps[pump_id]["job"] = value
            elif "_calibration_date" in key:
                pump_id = int(key.replace("pump_", "").replace("_calibration_date", ""))
                if pump_id not in pumps:
                    pumps[pump_id] = {}
                pumps[pump_id]["calibration_date"] = value

        return pumps

    # =========================================================================
    # EC/pH SENSOR STATE TRACKING
    # =========================================================================

    def set_ecph_monitoring(self, is_active: bool) -> bool:
        """Set EC/pH monitoring active state."""
        return self.set("ecph_monitoring_active", is_active)

    def get_ecph_monitoring(self) -> bool:
        """Get EC/pH monitoring active state."""
        return self.get("ecph_monitoring_active", False)

    def set_ecph_values(self, ec: float, ph: float) -> bool:
        """
        Set current EC and pH values.

        Args:
            ec: EC value (electrical conductivity)
            ph: pH value
        """
        return self.set("ecph_current_values", {
            "ec": ec,
            "ph": ph,
            "timestamp": datetime.now().isoformat()
        })

    def get_ecph_values(self) -> Optional[Dict[str, Any]]:
        """Get current EC/pH values with timestamp."""
        return self.get("ecph_current_values")

    def set_ec_calibration_date(self, date_iso: str) -> bool:
        """Set EC sensor last calibration date (ISO format)."""
        return self.set("ec_calibration_date", date_iso)

    def get_ec_calibration_date(self) -> Optional[str]:
        """Get EC sensor last calibration date."""
        return self.get("ec_calibration_date")

    def set_ph_calibration_date(self, date_iso: str) -> bool:
        """Set pH sensor last calibration date (ISO format)."""
        return self.set("ph_calibration_date", date_iso)

    def get_ph_calibration_date(self) -> Optional[str]:
        """Get pH sensor last calibration date."""
        return self.get("ph_calibration_date")

    def get_ecph_status(self) -> Dict[str, Any]:
        """
        Get complete EC/pH sensor status.

        Returns:
            Dict with monitoring state, current values, and calibration dates
        """
        values = self.get_ecph_values() or {}
        return {
            "monitoring_active": self.get_ecph_monitoring(),
            "ec": values.get("ec", 0.0),
            "ph": values.get("ph", 0.0),
            "last_reading": values.get("timestamp"),
            "ec_calibration_date": self.get_ec_calibration_date(),
            "ph_calibration_date": self.get_ph_calibration_date()
        }

    # =========================================================================
    # FLOW METER STATE TRACKING
    # =========================================================================

    def set_flow_meter_state(self, flow_id: int, is_active: bool) -> bool:
        """Set flow meter active state (monitoring or not)."""
        return self.set(f"flow_{flow_id}_active", is_active)

    def get_flow_meter_state(self, flow_id: int) -> bool:
        """Get flow meter active state. Returns False if unknown."""
        return self.get(f"flow_{flow_id}_active", False)

    def set_flow_meter_job(self, flow_id: int, job_data: Dict[str, Any]) -> bool:
        """
        Set current flow meter job data.

        Args:
            flow_id: Flow meter ID
            job_data: Dict with keys:
                - target_gallons: Target volume for this operation
                - gallons_measured: Volume measured so far
                - operation_type: 'fill' or 'send'
                - tank_id: Associated tank ID
                - job_id: Optional job identifier
                - started_at: ISO timestamp when job started
        """
        return self.set(f"flow_{flow_id}_job", job_data)

    def get_flow_meter_job(self, flow_id: int) -> Optional[Dict[str, Any]]:
        """Get current flow meter job data."""
        return self.get(f"flow_{flow_id}_job")

    def clear_flow_meter_job(self, flow_id: int) -> bool:
        """Clear flow meter job data (call when job completes)."""
        return self.delete(f"flow_{flow_id}_job")

    def set_flow_meter_total(self, flow_id: int, total_gallons: float) -> bool:
        """Set flow meter lifetime total gallons measured."""
        return self.set(f"flow_{flow_id}_total_gallons", total_gallons)

    def get_flow_meter_total(self, flow_id: int) -> float:
        """Get flow meter lifetime total gallons. Returns 0.0 if unknown."""
        return self.get(f"flow_{flow_id}_total_gallons", 0.0)

    def increment_flow_meter_total(self, flow_id: int, gallons: float) -> bool:
        """Increment flow meter total by specified gallons."""
        current = self.get_flow_meter_total(flow_id)
        return self.set_flow_meter_total(flow_id, current + gallons)

    def set_flow_meter_calibration(self, flow_id: int, pulses_per_gallon: int) -> bool:
        """Set flow meter calibration (pulses per gallon)."""
        return self.set(f"flow_{flow_id}_calibration", pulses_per_gallon)

    def get_flow_meter_calibration(self, flow_id: int) -> Optional[int]:
        """Get flow meter calibration."""
        return self.get(f"flow_{flow_id}_calibration")

    def get_all_flow_meters(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all flow meter states as {flow_id: {active, job, total_gallons, calibration}}.
        """
        flows = {}
        raw = self.get_prefix("flow_")

        # Group by flow_id
        for key, value in raw.items():
            if "_active" in key:
                flow_id = int(key.replace("flow_", "").replace("_active", ""))
                if flow_id not in flows:
                    flows[flow_id] = {}
                flows[flow_id]["active"] = value
            elif "_job" in key:
                flow_id = int(key.replace("flow_", "").replace("_job", ""))
                if flow_id not in flows:
                    flows[flow_id] = {}
                flows[flow_id]["job"] = value
            elif "_total_gallons" in key:
                flow_id = int(key.replace("flow_", "").replace("_total_gallons", ""))
                if flow_id not in flows:
                    flows[flow_id] = {}
                flows[flow_id]["total_gallons"] = value
            elif "_calibration" in key:
                flow_id = int(key.replace("flow_", "").replace("_calibration", ""))
                if flow_id not in flows:
                    flows[flow_id] = {}
                flows[flow_id]["calibration"] = value

        return flows

    # =========================================================================
    # JOB HISTORY TRACKING (Uses direct DB access - less frequent operations)
    # =========================================================================

    def log_job_start(self, job_type: str, tank_id: int = None, room_id: str = None,
                      target_value: float = None, parameters: Dict[str, Any] = None) -> int:
        """
        Log the start of a job. Returns the job_id for later updates.

        Args:
            job_type: Type of job ('fill', 'mix', 'send')
            tank_id: Tank ID (optional)
            room_id: Room ID for send jobs (optional)
            target_value: Target gallons, ml, or seconds depending on job type
            parameters: Additional job parameters as dict

        Returns:
            job_id: The ID of the created job record
        """
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.execute('''
                    INSERT INTO job_history
                    (job_type, status, tank_id, room_id, target_value, parameters, started_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_type,
                    'running',
                    tank_id,
                    room_id,
                    target_value,
                    json.dumps(parameters) if parameters else None,
                    datetime.now().isoformat()
                ))
                return cursor.lastrowid
        except Exception as e:
            print(f"[StateManager] Error logging job start: {e}")
            return -1

    def log_job_complete(self, job_id: int, status: str = 'completed',
                        actual_value: float = None, error_message: str = None) -> bool:
        """
        Log the completion of a job.

        Args:
            job_id: The job ID returned from log_job_start
            status: Final status ('completed', 'failed', 'stopped')
            actual_value: Actual value achieved (gallons, ml, etc.)
            error_message: Error message if failed

        Returns:
            True if successful
        """
        try:
            with self._pool.get_connection() as conn:
                # Get start time to calculate duration
                row = conn.execute(
                    "SELECT started_at FROM job_history WHERE id = ?", (job_id,)
                ).fetchone()

                if row:
                    started_at = datetime.fromisoformat(row['started_at'])
                    completed_at = datetime.now()
                    duration = (completed_at - started_at).total_seconds()

                    conn.execute('''
                        UPDATE job_history
                        SET status = ?, actual_value = ?, error_message = ?,
                            completed_at = ?, duration_seconds = ?
                        WHERE id = ?
                    ''', (
                        status,
                        actual_value,
                        error_message,
                        completed_at.isoformat(),
                        duration,
                        job_id
                    ))
                    return True
            return False
        except Exception as e:
            print(f"[StateManager] Error logging job complete: {e}")
            return False

    def get_job_history(self, limit: int = 50, job_type: str = None,
                       status: str = None, tank_id: int = None) -> List[Dict[str, Any]]:
        """
        Get job history with optional filters.

        Args:
            limit: Maximum number of records to return
            job_type: Filter by job type ('fill', 'mix', 'send')
            status: Filter by status ('completed', 'failed', 'stopped', 'running')
            tank_id: Filter by tank ID

        Returns:
            List of job records as dicts
        """
        try:
            with self._pool.get_connection() as conn:
                query = "SELECT * FROM job_history WHERE 1=1"
                params = []

                if job_type:
                    query += " AND job_type = ?"
                    params.append(job_type)
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if tank_id:
                    query += " AND tank_id = ?"
                    params.append(tank_id)

                query += " ORDER BY started_at DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(query, params).fetchall()

                result = []
                for row in rows:
                    job = dict(row)
                    # Parse parameters JSON
                    if job.get('parameters'):
                        try:
                            job['parameters'] = json.loads(job['parameters'])
                        except json.JSONDecodeError:
                            pass
                    result.append(job)

                return result

        except Exception as e:
            print(f"[StateManager] Error getting job history: {e}")
            return []

    def get_job_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get job statistics for the specified number of days.

        Args:
            days: Number of days to include in stats

        Returns:
            Dict with job statistics
        """
        try:
            with self._pool.get_connection() as conn:
                cutoff = datetime.now().isoformat()[:10]  # Get date part only

                # Use a single query with GROUP BY for efficiency
                stats_query = '''
                    SELECT
                        job_type,
                        status,
                        COUNT(*) as count,
                        AVG(CASE WHEN status = 'completed' THEN duration_seconds END) as avg_duration
                    FROM job_history
                    WHERE date(started_at) >= date(?, '-' || ? || ' days')
                    GROUP BY job_type, status
                '''
                rows = conn.execute(stats_query, (cutoff, days)).fetchall()

                # Process results
                status_counts = {'completed': 0, 'failed': 0, 'stopped': 0, 'running': 0}
                type_counts = {'fill': 0, 'mix': 0, 'send': 0}
                avg_durations = {'fill': 0, 'mix': 0, 'send': 0}
                total = 0

                for row in rows:
                    job_type = row['job_type']
                    status = row['status']
                    count = row['count']

                    if status in status_counts:
                        status_counts[status] += count
                    if job_type in type_counts:
                        type_counts[job_type] += count
                    if row['avg_duration'] and job_type in avg_durations:
                        avg_durations[job_type] = round(row['avg_duration'], 1)
                    total += count

                return {
                    'period_days': days,
                    'total_jobs': total,
                    'by_status': status_counts,
                    'by_type': type_counts,
                    'avg_duration_seconds': avg_durations,
                    'success_rate': round(
                        (status_counts['completed'] / total * 100) if total > 0 else 0, 1
                    )
                }

        except Exception as e:
            print(f"[StateManager] Error getting job stats: {e}")
            return {}

    def clear_job_history(self, older_than_days: int = None) -> bool:
        """
        Clear job history. Optionally only clear records older than specified days.

        Args:
            older_than_days: If provided, only clear records older than this many days

        Returns:
            True if successful
        """
        try:
            with self._pool.get_connection() as conn:
                if older_than_days:
                    cutoff = datetime.now().isoformat()[:10]
                    conn.execute('''
                        DELETE FROM job_history
                        WHERE date(started_at) < date(?, '-' || ? || ' days')
                    ''', (cutoff, older_than_days))
                else:
                    conn.execute("DELETE FROM job_history")
            return True
        except Exception as e:
            print(f"[StateManager] Error clearing job history: {e}")
            return False


# =============================================================================
# GLOBAL INSTANCE - Import this for easy access
# =============================================================================

state = StateManager()


# =============================================================================
# FLASK INTEGRATION HELPERS
# =============================================================================

def init_state_from_hardware(relay_states: Dict[int, bool] = None):
    """
    Initialize state DB from current hardware state.
    Call this on Flask startup after reading GPIO states.

    Args:
        relay_states: Dict of {relay_id: is_on} from RelayController
    """
    if relay_states:
        for relay_id, is_on in relay_states.items():
            state.set_relay(relay_id, is_on)
        print(f"[StateManager] Initialized {len(relay_states)} relay states from hardware")


def get_system_snapshot() -> Dict[str, Any]:
    """
    Get a snapshot of all hardware state for API responses.

    Returns:
        Dict with relays, tanks, pumps, flow meters, ec/ph sensors, and processes
    """
    return {
        "relays": state.get_all_relays(),
        "tanks": {
            int(k.replace("tank_", "").replace("_state", "")): v
            for k, v in state.get_prefix("tank_").items()
            if "_state" in k
        },
        "pumps": state.get_all_pumps(),
        "flow_meters": state.get_all_flow_meters(),
        "ecph": state.get_ecph_status(),
        "processes": state.get_active_processes(),
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# CLI FOR DEBUGGING
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Hardware State Manager (High-Performance Version)")
        print("-" * 50)
        print("\nFeatures:")
        print("  - In-memory cache for instant access")
        print("  - Async SQLite persistence")
        print("  - WAL mode for concurrency")
        print("  - Connection pooling")
        print("\nCurrent state:")
        for key, value in state.get_all().items():
            print(f"  {key}: {value}")
        print("\nUsage:")
        print("  python state_manager.py get <key>")
        print("  python state_manager.py set <key> <value>")
        print("  python state_manager.py delete <key>")
        print("  python state_manager.py stress  # Stress test")
        print("  python state_manager.py clear")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "get" and len(sys.argv) >= 3:
        key = sys.argv[2]
        print(f"{key}: {state.get(key, '(not set)')}")

    elif cmd == "set" and len(sys.argv) >= 4:
        key, value = sys.argv[2], sys.argv[3]
        state.set(key, value)
        print(f"Set {key} = {value}")

    elif cmd == "delete" and len(sys.argv) >= 3:
        key = sys.argv[2]
        state.delete(key)
        print(f"Deleted {key}")

    elif cmd == "stress":
        import time
        print("Running stress test: 100 rapid relay toggles...")
        start = time.time()
        for i in range(100):
            state.set_relay(1, i % 2 == 0)
        elapsed = time.time() - start
        print(f"Completed 100 toggles in {elapsed:.3f} seconds")
        print(f"Average: {elapsed/100*1000:.2f}ms per operation")
        # Wait for persistence
        time.sleep(0.5)
        print("Persistence complete. Final state:")
        print(f"  relay_1: {state.get_relay(1)}")

    elif cmd == "clear":
        confirm = input("Clear ALL state? (yes/no): ")
        if confirm.lower() == "yes":
            with state._pool.get_connection() as conn:
                conn.execute("DELETE FROM state")
            print("Cleared all state")

    else:
        print(f"Unknown command: {cmd}")

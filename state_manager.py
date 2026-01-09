"""
Local SQLite State Manager for Hardware State Persistence

Keeps hardware states (relay on/off, tank status, process progress) in a local
SQLite database for fast access and persistence across Flask restarts.

For analytics and historical data, use Supabase. This is just for snappy
local state that needs to survive restarts.

Usage:
    from state_manager import state
    
    # Simple key-value
    state.set("relay_1", "on")
    current = state.get("relay_1", default="off")
    
    # Bulk operations
    state.set_many({"relay_1": "on", "relay_2": "off", "tank_1": "filling"})
    all_relays = state.get_prefix("relay_")
    
    # Check what's stored
    state.get_all()
"""

import sqlite3
import threading
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

# Database location - in the project root, survives restarts
DEFAULT_DB_PATH = Path(__file__).parent / "hardware_state.db"


class StateManager:
    """Thread-safe SQLite state manager for hardware state persistence."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DEFAULT_DB_PATH)
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self._get_conn() as conn:
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
    
    @contextmanager
    def _get_conn(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a state value. Converts non-strings to JSON.
        
        Args:
            key: State key (e.g., "relay_1", "tank_1_state")
            value: Any JSON-serializable value
            
        Returns:
            True if successful
        """
        with self._lock:
            try:
                # Convert non-strings to JSON
                if not isinstance(value, str):
                    value = json.dumps(value)
                
                with self._get_conn() as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO state (key, value, updated_at)
                        VALUES (?, ?, ?)
                    ''', (key, value, datetime.now().isoformat()))
                return True
            except Exception as e:
                print(f"[StateManager] Error setting {key}: {e}")
                return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a state value.

        Args:
            key: State key
            default: Value to return if key doesn't exist

        Returns:
            The stored value, or default if not found
        """
        with self._lock:
            try:
                with self._get_conn() as conn:
                    row = conn.execute(
                        "SELECT value FROM state WHERE key = ?", (key,)
                    ).fetchone()

                    if row is None:
                        return default

                    value = row['value']

                    # Try to parse as JSON, fall back to string
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value

            except Exception as e:
                print(f"[StateManager] Error getting {key}: {e}")
                return default
    
    def delete(self, key: str) -> bool:
        """Delete a state key."""
        with self._lock:
            try:
                with self._get_conn() as conn:
                    conn.execute("DELETE FROM state WHERE key = ?", (key,))
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
        with self._lock:
            try:
                with self._get_conn() as conn:
                    now = datetime.now().isoformat()
                    for key, value in items.items():
                        if not isinstance(value, str):
                            value = json.dumps(value)
                        conn.execute('''
                            INSERT OR REPLACE INTO state (key, value, updated_at)
                            VALUES (?, ?, ?)
                        ''', (key, value, now))
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
        with self._lock:
            try:
                with self._get_conn() as conn:
                    rows = conn.execute(
                        "SELECT key, value FROM state WHERE key LIKE ?",
                        (f"{prefix}%",)
                    ).fetchall()

                    result = {}
                    for row in rows:
                        value = row['value']
                        try:
                            value = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            pass
                        result[row['key']] = value

                    return result

            except Exception as e:
                print(f"[StateManager] Error in get_prefix: {e}")
                return {}
    
    def get_all(self) -> Dict[str, Any]:
        """Get all stored state."""
        return self.get_prefix("")
    
    def clear_prefix(self, prefix: str) -> bool:
        """Delete all keys with a given prefix."""
        with self._lock:
            try:
                with self._get_conn() as conn:
                    conn.execute(
                        "DELETE FROM state WHERE key LIKE ?",
                        (f"{prefix}%",)
                    )
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
    # JOB HISTORY TRACKING
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
        with self._lock:
            try:
                with self._get_conn() as conn:
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
        with self._lock:
            try:
                with self._get_conn() as conn:
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
        with self._lock:
            try:
                with self._get_conn() as conn:
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
        with self._lock:
            try:
                with self._get_conn() as conn:
                    cutoff = datetime.now().isoformat()[:10]  # Get date part only

                    # Get counts by status
                    status_counts = {}
                    for status in ['completed', 'failed', 'stopped', 'running']:
                        row = conn.execute('''
                            SELECT COUNT(*) as count FROM job_history
                            WHERE status = ? AND date(started_at) >= date(?, '-' || ? || ' days')
                        ''', (status, cutoff, days)).fetchone()
                        status_counts[status] = row['count'] if row else 0

                    # Get counts by type
                    type_counts = {}
                    for job_type in ['fill', 'mix', 'send']:
                        row = conn.execute('''
                            SELECT COUNT(*) as count FROM job_history
                            WHERE job_type = ? AND date(started_at) >= date(?, '-' || ? || ' days')
                        ''', (job_type, cutoff, days)).fetchone()
                        type_counts[job_type] = row['count'] if row else 0

                    # Get average duration by type for completed jobs
                    avg_durations = {}
                    for job_type in ['fill', 'mix', 'send']:
                        row = conn.execute('''
                            SELECT AVG(duration_seconds) as avg_duration FROM job_history
                            WHERE job_type = ? AND status = 'completed'
                            AND date(started_at) >= date(?, '-' || ? || ' days')
                        ''', (job_type, cutoff, days)).fetchone()
                        avg_durations[job_type] = round(row['avg_duration'], 1) if row and row['avg_duration'] else 0

                    # Total jobs
                    row = conn.execute('''
                        SELECT COUNT(*) as total FROM job_history
                        WHERE date(started_at) >= date(?, '-' || ? || ' days')
                    ''', (cutoff, days)).fetchone()
                    total = row['total'] if row else 0

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
        with self._lock:
            try:
                with self._get_conn() as conn:
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
        print("Hardware State Manager")
        print("-" * 40)
        print("\nCurrent state:")
        for key, value in state.get_all().items():
            print(f"  {key}: {value}")
        print("\nUsage:")
        print("  python state_manager.py get <key>")
        print("  python state_manager.py set <key> <value>")
        print("  python state_manager.py delete <key>")
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
    
    elif cmd == "clear":
        confirm = input("Clear ALL state? (yes/no): ")
        if confirm.lower() == "yes":
            with state._get_conn() as conn:
                conn.execute("DELETE FROM state")
            print("Cleared all state")
    
    else:
        print(f"Unknown command: {cmd}")
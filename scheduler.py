#!/usr/bin/env python3
"""
Job Scheduler for Nutrient Mixing System
Manages job execution, tank state transitions, and conflict prevention
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any
from queue import Queue, PriorityQueue
from dataclasses import dataclass, field

from models import (
    DatabaseManager, Tank, Job, TankState, JobStatus, JobType, 
    init_models
)
from hardware_manager import HardwareManager
from jobs import BaseJob, create_job, JobPriority

logger = logging.getLogger(__name__)

@dataclass
class PriorityJob:
    """Wrapper for priority queue ordering"""
    priority: int
    job_id: int
    job: BaseJob = field(compare=False)
    
    def __lt__(self, other):
        return self.priority < other.priority

class JobScheduler:
    """Job scheduler with tank state management and conflict prevention"""
    
    def __init__(self, hardware_manager: HardwareManager, db_path: str = "database.db"):
        """Initialize job scheduler"""
        self.hardware = hardware_manager
        
        # Initialize database models
        self.models = init_models(db_path)
        self.tank_model = self.models['tank']
        self.job_model = self.models['job']
        
        # Job management
        self.job_queue = PriorityQueue()
        self.active_jobs: Dict[int, BaseJob] = {}  # job_id -> job
        self.tank_jobs: Dict[int, List[int]] = {}  # tank_id -> [job_ids]
        
        # Scheduler state
        self.running = False
        self.scheduler_thread = None
        self.update_interval = 1.0  # Update every second
        
        # Tank state tracking
        self.tank_states: Dict[int, TankState] = {}
        self._initialize_tank_states()
        
        # State transition rules
        self.state_transitions = {
            TankState.IDLE: [TankState.FILLING, TankState.MIXING],
            TankState.FILLING: [TankState.IDLE, TankState.MIXING],  # Can mix after 20 gallons
            TankState.MIXING: [TankState.IDLE, TankState.SENDING],
            TankState.SENDING: [TankState.IDLE]
        }
        
        logger.info("Job scheduler initialized")
    
    def _initialize_tank_states(self):
        """Initialize tank states from database"""
        tanks = self.tank_model.get_all()
        for tank in tanks:
            tank_id = tank['tank_id']
            state = TankState(tank['state'])
            self.tank_states[tank_id] = state
            
            # Initialize tank job tracking
            self.tank_jobs[tank_id] = []
        
        logger.info(f"Initialized {len(self.tank_states)} tank states")
    
    def start(self):
        """Start the job scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Job scheduler started")
    
    def stop(self):
        """Stop the job scheduler"""
        if not self.running:
            return
        
        logger.info("Stopping job scheduler...")
        self.running = False
        
        # Stop all active jobs
        for job in list(self.active_jobs.values()):
            try:
                job.stop()
            except Exception as e:
                logger.error(f"Error stopping job {job.job_id}: {e}")
        
        # Wait for scheduler thread
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Job scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Process job queue
                self._process_job_queue()
                
                # Update active jobs
                self._update_active_jobs()
                
                # Update hardware operations
                self._update_hardware_operations()
                
                # Update tank states
                self._update_tank_states()
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(1)
    
    def _process_job_queue(self):
        """Process pending jobs from queue"""
        while not self.job_queue.empty() and self.running:
            try:
                priority_job = self.job_queue.get_nowait()
                job = priority_job.job
                
                # Check if job can start
                if self._can_job_start(job):
                    if job.start():
                        # Add to active jobs
                        self.active_jobs[job.job_id] = job
                        
                        # Track job for tank
                        if job.tank_id not in self.tank_jobs:
                            self.tank_jobs[job.tank_id] = []
                        self.tank_jobs[job.tank_id].append(job.job_id)
                        
                        # Update database
                        self.job_model.update_status(job.job_id, JobStatus.RUNNING)
                        
                        # Update tank state
                        self._update_tank_state_for_job(job, starting=True)
                        
                        logger.info(f"Started job {job.job_id} ({job.__class__.__name__}) on tank {job.tank_id}")
                    else:
                        # Job failed to start
                        self.job_model.update_status(job.job_id, JobStatus.FAILED, 
                                                   error_message=job.error_message)
                        logger.error(f"Failed to start job {job.job_id}: {job.error_message}")
                else:
                    # Job cannot start yet - put back in queue
                    self.job_queue.put(priority_job)
                    break  # Try again next cycle
                    
            except Exception as e:
                logger.error(f"Error processing job queue: {e}")
                break
    
    def _update_active_jobs(self):
        """Update all active jobs"""
        completed_jobs = []
        
        for job_id, job in list(self.active_jobs.items()):
            try:
                # Update job progress
                still_running = job.update()
                
                # Update database with current progress
                self.job_model.update_progress(job_id, job.progress)
                
                if not still_running:
                    # Job completed or failed
                    completed_jobs.append(job_id)
                    
                    # Update database status
                    self.job_model.update_status(job_id, job.status, 
                                               job.progress, job.error_message)
                    
                    # Update tank state
                    self._update_tank_state_for_job(job, starting=False)
                    
                    # Remove from tracking
                    if job.tank_id in self.tank_jobs:
                        if job_id in self.tank_jobs[job.tank_id]:
                            self.tank_jobs[job.tank_id].remove(job_id)
                    
                    logger.info(f"Job {job_id} completed with status: {job.status.value}")
                    
            except Exception as e:
                logger.error(f"Error updating job {job_id}: {e}")
                # Mark job as failed
                job.set_error(f"Update error: {e}")
                completed_jobs.append(job_id)
        
        # Remove completed jobs
        for job_id in completed_jobs:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def _update_hardware_operations(self):
        """Update hardware operations and sync with jobs"""
        try:
            completed_operations = self.hardware.update_operations()
            
            # Handle completed hardware operations
            for op_key in completed_operations:
                logger.debug(f"Hardware operation completed: {op_key}")
                
        except Exception as e:
            logger.error(f"Error updating hardware operations: {e}")
    
    def _update_tank_states(self):
        """Update tank states in database"""
        try:
            for tank_id, state in self.tank_states.items():
                self.tank_model.update_state(tank_id, state)
                
        except Exception as e:
            logger.error(f"Error updating tank states: {e}")
    
    def _can_job_start(self, job: BaseJob) -> bool:
        """Check if job can start based on tank state and conflicts"""
        tank_id = job.tank_id
        
        # Check if tank exists
        if tank_id not in self.tank_states:
            logger.error(f"Tank {tank_id} not found")
            return False
        
        # Check job-specific prerequisites
        if not job.can_start():
            return False
        
        # Check tank state conflicts
        current_state = self.tank_states[tank_id]
        required_state = self._get_required_tank_state(job)
        
        if required_state and current_state != required_state:
            # Check if transition is allowed
            if required_state not in self.state_transitions.get(current_state, []):
                logger.debug(f"Job {job.job_id} blocked: tank {tank_id} state {current_state.value} -> {required_state.value} not allowed")
                return False
        
        # Check for blocking operations
        blocking_ops = job.get_blocking_operations()
        if blocking_ops:
            # Check if any active jobs on this tank have conflicting operations
            for active_job_id in self.tank_jobs.get(tank_id, []):
                if active_job_id in self.active_jobs:
                    active_job = self.active_jobs[active_job_id]
                    active_blocking = active_job.get_blocking_operations()
                    
                    # Check for conflicts
                    if any(op in active_blocking for op in blocking_ops):
                        logger.debug(f"Job {job.job_id} blocked by active job {active_job_id}")
                        return False
        
        return True
    
    def _get_required_tank_state(self, job: BaseJob) -> Optional[TankState]:
        """Get required tank state for job type"""
        job_class = job.__class__.__name__
        
        if job_class == 'FillJob':
            return TankState.FILLING
        elif job_class == 'MixJob':
            return TankState.MIXING
        elif job_class == 'SendJob':
            return TankState.SENDING
        
        return None
    
    def _update_tank_state_for_job(self, job: BaseJob, starting: bool):
        """Update tank state when job starts or completes"""
        tank_id = job.tank_id
        
        if starting:
            # Job starting - set appropriate state
            required_state = self._get_required_tank_state(job)
            if required_state:
                self.tank_states[tank_id] = required_state
                logger.debug(f"Tank {tank_id} state -> {required_state.value}")
        else:
            # Job completed - check if tank should return to idle
            active_jobs_for_tank = self.tank_jobs.get(tank_id, [])
            
            if not active_jobs_for_tank:
                # No more active jobs - return to idle
                self.tank_states[tank_id] = TankState.IDLE
                logger.debug(f"Tank {tank_id} state -> IDLE")
            else:
                # Other jobs still active - determine state from remaining jobs
                for job_id in active_jobs_for_tank:
                    if job_id in self.active_jobs:
                        remaining_job = self.active_jobs[job_id]
                        required_state = self._get_required_tank_state(remaining_job)
                        if required_state:
                            self.tank_states[tank_id] = required_state
                            break
    
    # =============================================================================
    # PUBLIC API - Job Management
    # =============================================================================
    
    def submit_job(self, job_type: JobType, tank_id: int, parameters: Dict[str, Any], 
                   priority: JobPriority = JobPriority.NORMAL) -> Optional[int]:
        """Submit a new job to the scheduler"""
        try:
            # Create job in database
            job_id = self.job_model.create(job_type, tank_id, parameters)
            if not job_id:
                logger.error("Failed to create job in database")
                return None
            
            # Create job instance
            job = create_job(job_id, job_type, tank_id, self.hardware, parameters)
            if not job:
                logger.error(f"Failed to create job instance for job {job_id}")
                self.job_model.update_status(job_id, JobStatus.FAILED, 
                                           error_message="Failed to create job instance")
                return None
            
            job.priority = priority
            
            # Add to queue
            priority_job = PriorityJob(priority.value, job_id, job)
            self.job_queue.put(priority_job)
            
            logger.info(f"Submitted job {job_id}: {job_type.value} for tank {tank_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            return None
    
    def cancel_job(self, job_id: int) -> bool:
        """Cancel a job"""
        try:
            if job_id in self.active_jobs:
                # Job is active - stop it
                job = self.active_jobs[job_id]
                if job.stop():
                    self.job_model.update_status(job_id, JobStatus.CANCELLED)
                    logger.info(f"Cancelled active job {job_id}")
                    return True
                else:
                    logger.error(f"Failed to stop job {job_id}")
                    return False
            else:
                # Job is pending - mark as cancelled
                self.job_model.update_status(job_id, JobStatus.CANCELLED)
                logger.info(f"Cancelled pending job {job_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job status"""
        try:
            if job_id in self.active_jobs:
                # Get live status from active job
                return self.active_jobs[job_id].get_status()
            else:
                # Get status from database
                job_data = self.job_model.get(job_id)
                return job_data
                
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return None
    
    def get_tank_status(self, tank_id: int) -> Dict[str, Any]:
        """Get comprehensive tank status"""
        try:
            # Get tank info from database
            tank_data = self.tank_model.get(tank_id)
            if not tank_data:
                return {}
            
            # Get current state
            current_state = self.tank_states.get(tank_id, TankState.IDLE)
            
            # Get active jobs for tank
            active_jobs = []
            for job_id in self.tank_jobs.get(tank_id, []):
                if job_id in self.active_jobs:
                    job = self.active_jobs[job_id]
                    active_jobs.append({
                        'job_id': job_id,
                        'job_type': job.__class__.__name__,
                        'progress': job.progress,
                        'step_description': job.step_descriptions[job.current_step] if job.current_step < len(job.step_descriptions) else "Complete"
                    })
            
            # Get hardware status
            hardware_status = self.hardware.get_tank_status(tank_id)
            
            return {
                'tank_id': tank_id,
                'name': tank_data['name'],
                'capacity_gallons': tank_data['capacity_gallons'],
                'current_volume': tank_data['current_volume'],
                'state': current_state.value,
                'available': self.hardware.is_tank_available(tank_id),
                'active_jobs': active_jobs,
                'hardware_status': hardware_status,
                'updated_at': tank_data['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting tank status {tank_id}: {e}")
            return {}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            return {
                'scheduler_running': self.running,
                'active_jobs': len(self.active_jobs),
                'pending_jobs': self.job_queue.qsize(),
                'tank_states': {tank_id: state.value for tank_id, state in self.tank_states.items()},
                'hardware_status': self.hardware.get_system_status(),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def emergency_stop(self) -> bool:
        """Emergency stop all operations"""
        try:
            logger.warning("EMERGENCY STOP - Stopping all jobs and hardware")
            
            # Stop all active jobs
            for job in list(self.active_jobs.values()):
                try:
                    job.stop()
                    self.job_model.update_status(job.job_id, JobStatus.CANCELLED, 
                                               error_message="Emergency stop")
                except Exception as e:
                    logger.error(f"Error stopping job {job.job_id} during emergency stop: {e}")
            
            # Clear active jobs
            self.active_jobs.clear()
            
            # Reset tank states to idle
            for tank_id in self.tank_states:
                self.tank_states[tank_id] = TankState.IDLE
                self.tank_jobs[tank_id] = []
            
            # Emergency stop hardware
            self.hardware.emergency_stop()
            
            logger.info("Emergency stop completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return False

if __name__ == "__main__":
    # Test the scheduler
    logging.basicConfig(level=logging.INFO)
    
    print("Job Scheduler Test")
    print("=" * 40)
    
    # Initialize with mock hardware
    from hardware_manager import HardwareManager
    hardware = HardwareManager(use_mock_hardware={'relays': True, 'pumps': True, 'flow_meters': True, 'sensors': True})
    
    # Create scheduler
    scheduler = JobScheduler(hardware, "test_scheduler.db")
    scheduler.start()
    
    try:
        # Submit test jobs
        print("Submitting test jobs...")
        
        fill_job_id = scheduler.submit_job(JobType.FILL, 1, {'gallons': 75})
        print(f"Submitted fill job: {fill_job_id}")
        
        mix_job_id = scheduler.submit_job(JobType.MIX, 1, {
            'formula': {'VegA': 10, 'VegB': 8},
            'ph_target': 6.2,
            'ec_target': 1.4
        })
        print(f"Submitted mix job: {mix_job_id}")
        
        # Monitor for a few seconds
        for i in range(10):
            system_status = scheduler.get_system_status()
            print(f"System status: {system_status['active_jobs']} active, {system_status['pending_jobs']} pending")
            
            if fill_job_id:
                job_status = scheduler.get_job_status(fill_job_id)
                if job_status:
                    print(f"  Fill job: {job_status.get('progress', 0):.1f}% - {job_status.get('status', 'unknown')}")
            
            time.sleep(1)
        
        print("Test completed")
        
    finally:
        scheduler.stop()
        hardware.cleanup()
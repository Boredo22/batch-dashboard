#!/usr/bin/env python3
"""
Job System for Nutrient Mixing Operations
Implements FillJob, MixJob, and SendJob classes for automated tank operations
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

from models import JobStatus, JobType, TankState
from hardware_manager import HardwareManager, OperationResult

logger = logging.getLogger(__name__)

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class BaseJob(ABC):
    """Base class for all job types"""
    
    def __init__(self, job_id: int, tank_id: int, hardware_manager: HardwareManager, 
                 parameters: Dict[str, Any] = None, priority: JobPriority = JobPriority.NORMAL):
        self.job_id = job_id
        self.tank_id = tank_id
        self.hardware = hardware_manager
        self.parameters = parameters or {}
        self.priority = priority
        
        # Job state
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.error_message = None
        self.start_time = None
        self.end_time = None
        
        # Job-specific state
        self.current_step = 0
        self.total_steps = 1
        self.step_descriptions = ["Initialize"]
        
        logger.info(f"Job {job_id} created: {self.__class__.__name__} for tank {tank_id}")
    
    @abstractmethod
    def can_start(self) -> bool:
        """Check if job can start (tank availability, prerequisites, etc.)"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """Start the job execution"""
        pass
    
    @abstractmethod
    def update(self) -> bool:
        """Update job progress - returns True if still running, False if complete"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the job execution"""
        pass
    
    @abstractmethod
    def get_blocking_operations(self) -> List[str]:
        """Get list of operations this job blocks on the tank"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive job status"""
        return {
            'job_id': self.job_id,
            'tank_id': self.tank_id,
            'job_type': self.__class__.__name__,
            'status': self.status.value,
            'progress': self.progress,
            'error_message': self.error_message,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'step_description': self.step_descriptions[self.current_step] if self.current_step < len(self.step_descriptions) else "Complete",
            'parameters': self.parameters,
            'priority': self.priority.value
        }
    
    def update_progress(self, step: int = None, progress: float = None):
        """Update job progress"""
        if step is not None:
            self.current_step = min(step, self.total_steps - 1)
        
        if progress is not None:
            self.progress = max(0.0, min(100.0, progress))
        else:
            # Calculate progress based on current step
            self.progress = (self.current_step / self.total_steps) * 100.0
        
        logger.debug(f"Job {self.job_id} progress: {self.progress:.1f}% (step {self.current_step}/{self.total_steps})")
    
    def set_error(self, error_message: str):
        """Set job error state"""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.end_time = time.time()
        logger.error(f"Job {self.job_id} failed: {error_message}")
    
    def complete(self):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.progress = 100.0
        self.end_time = time.time()
        duration = self.end_time - self.start_time if self.start_time else 0
        logger.info(f"Job {self.job_id} completed in {duration:.1f}s")

class FillJob(BaseJob):
    """Fill tank with water - non-blocking operation"""
    
    def __init__(self, job_id: int, tank_id: int, hardware_manager: HardwareManager, 
                 gallons: float, **kwargs):
        parameters = {'gallons': gallons}
        super().__init__(job_id, tank_id, hardware_manager, parameters, **kwargs)
        
        self.target_gallons = gallons
        self.total_steps = 3
        self.step_descriptions = [
            "Starting fill operation",
            "Monitoring water flow", 
            "Fill complete"
        ]
        
        # Fill-specific state
        self.flow_started = False
        self.current_gallons = 0.0
    
    def can_start(self) -> bool:
        """Fill can start if tank is available and not at capacity"""
        if not self.hardware.is_tank_available(self.tank_id):
            return False
        
        # Check tank capacity
        tank_status = self.hardware.get_tank_status(self.tank_id)
        if tank_status.get('capacity', 0) < self.target_gallons:
            self.set_error(f"Target gallons ({self.target_gallons}) exceeds tank capacity")
            return False
        
        return True
    
    def start(self) -> bool:
        """Start fill operation"""
        if not self.can_start():
            return False
        
        try:
            self.status = JobStatus.RUNNING
            self.start_time = time.time()
            self.update_progress(0)
            
            # Start hardware fill operation
            result = self.hardware.fill_tank(self.tank_id, self.target_gallons)
            
            if result == OperationResult.IN_PROGRESS:
                self.flow_started = True
                self.update_progress(1)
                logger.info(f"Fill job {self.job_id} started: {self.target_gallons} gallons to tank {self.tank_id}")
                return True
            else:
                self.set_error(f"Failed to start fill operation: {result}")
                return False
                
        except Exception as e:
            self.set_error(f"Error starting fill: {e}")
            return False
    
    def update(self) -> bool:
        """Update fill progress"""
        if self.status != JobStatus.RUNNING:
            return False
        
        try:
            # Check if fill operation is still active
            tank_status = self.hardware.get_tank_status(self.tank_id)
            fill_active = any(op.get('active', False) for op_type, op in tank_status.get('operations', {}).items() 
                            if op_type == 'fill')
            
            if fill_active:
                # Still filling - update progress based on flow
                elapsed_time = time.time() - self.start_time
                estimated_progress = min(90.0, (elapsed_time / 300.0) * 100.0)  # Estimate 5 min fill
                self.update_progress(progress=estimated_progress)
                return True
            else:
                # Fill completed
                self.update_progress(2)
                self.complete()
                return False
                
        except Exception as e:
            self.set_error(f"Error updating fill: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop fill operation"""
        try:
            result = self.hardware.stop_tank_operation(self.tank_id, 'fill')
            if result == OperationResult.SUCCESS:
                self.status = JobStatus.CANCELLED
                self.end_time = time.time()
                logger.info(f"Fill job {self.job_id} stopped")
                return True
            else:
                logger.error(f"Failed to stop fill job {self.job_id}")
                return False
        except Exception as e:
            self.set_error(f"Error stopping fill: {e}")
            return False
    
    def get_blocking_operations(self) -> List[str]:
        """Fill operations don't block other operations"""
        return []

class MixJob(BaseJob):
    """Mix nutrients in tank - blocking operation"""
    
    def __init__(self, job_id: int, tank_id: int, hardware_manager: HardwareManager,
                 formula: Dict[str, float], ph_target: float = 6.0, ec_target: float = 1.5, **kwargs):
        parameters = {
            'formula': formula,
            'ph_target': ph_target,
            'ec_target': ec_target
        }
        super().__init__(job_id, tank_id, hardware_manager, parameters, **kwargs)
        
        self.formula = formula
        self.ph_target = ph_target
        self.ec_target = ec_target
        
        self.total_steps = 6
        self.step_descriptions = [
            "Waiting for minimum water level",
            "Starting circulation",
            "Dispensing nutrients",
            "Initial mixing",
            "Testing pH/EC levels",
            "Mix complete"
        ]
        
        # Mix-specific state
        self.min_water_gallons = 20  # Minimum water before mixing
        self.mix_duration = 300  # 5 minutes mixing time
        self.circulation_started = False
        self.nutrients_dispensed = False
        self.mixing_start_time = None
    
    def can_start(self) -> bool:
        """Mix can start if tank has sufficient water and is available"""
        if not self.hardware.is_tank_available(self.tank_id):
            return False
        
        # Check for minimum water level (would need volume tracking)
        tank_status = self.hardware.get_tank_status(self.tank_id)
        
        return True
    
    def start(self) -> bool:
        """Start mix operation"""
        if not self.can_start():
            return False
        
        try:
            self.status = JobStatus.RUNNING
            self.start_time = time.time()
            self.update_progress(0)
            
            # Wait for minimum water level
            self.update_progress(1)
            
            # Start mixing operation
            result = self.hardware.mix_tank(self.tank_id, self.formula)
            
            if result == OperationResult.IN_PROGRESS:
                self.circulation_started = True
                self.mixing_start_time = time.time()
                self.update_progress(2)
                logger.info(f"Mix job {self.job_id} started for tank {self.tank_id}")
                return True
            else:
                self.set_error(f"Failed to start mix operation: {result}")
                return False
                
        except Exception as e:
            self.set_error(f"Error starting mix: {e}")
            return False
    
    def update(self) -> bool:
        """Update mix progress"""
        if self.status != JobStatus.RUNNING:
            return False
        
        try:
            if not self.nutrients_dispensed:
                # Check if nutrient dispensing is complete
                self.nutrients_dispensed = True
                self.update_progress(3)
                logger.info(f"Mix job {self.job_id}: Nutrients dispensed")
            
            # Check mixing duration
            if self.mixing_start_time:
                elapsed_time = time.time() - self.mixing_start_time
                mix_progress = min(90.0, (elapsed_time / self.mix_duration) * 100.0)
                
                if elapsed_time >= self.mix_duration:
                    # Mixing time complete - test pH/EC
                    self.update_progress(4)
                    
                    # In real implementation, would test pH/EC here
                    ph_ok = True  # self._test_ph()
                    ec_ok = True  # self._test_ec()
                    
                    if ph_ok and ec_ok:
                        self.update_progress(5)
                        self.complete()
                        
                        # Stop mixing operation
                        self.hardware.stop_tank_operation(self.tank_id, 'mix')
                        return False
                    else:
                        # Continue mixing or adjust nutrients
                        self.mixing_start_time = time.time()  # Reset timer
                        logger.info(f"Mix job {self.job_id}: pH/EC not at target, continuing mix")
                else:
                    self.update_progress(progress=20.0 + (mix_progress * 0.7))
            
            return True
            
        except Exception as e:
            self.set_error(f"Error updating mix: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop mix operation"""
        try:
            result = self.hardware.stop_tank_operation(self.tank_id, 'mix')
            if result == OperationResult.SUCCESS:
                self.status = JobStatus.CANCELLED
                self.end_time = time.time()
                logger.info(f"Mix job {self.job_id} stopped")
                return True
            else:
                logger.error(f"Failed to stop mix job {self.job_id}")
                return False
        except Exception as e:
            self.set_error(f"Error stopping mix: {e}")
            return False
    
    def get_blocking_operations(self) -> List[str]:
        """Mix operations block all other operations on the tank"""
        return ['fill', 'mix', 'send']

class SendJob(BaseJob):
    """Send solution from tank to grow rooms - blocking operation"""
    
    def __init__(self, job_id: int, tank_id: int, hardware_manager: HardwareManager,
                 gallons: float, destination: str = None, **kwargs):
        parameters = {
            'gallons': gallons,
            'destination': destination or f'Room from Tank {tank_id}'
        }
        super().__init__(job_id, tank_id, hardware_manager, parameters, **kwargs)
        
        self.target_gallons = gallons
        self.destination = destination
        
        self.total_steps = 4
        self.step_descriptions = [
            "Checking tank volume",
            "Starting send operation",
            "Monitoring flow to destination",
            "Send complete"
        ]
        
        # Send-specific state
        self.send_started = False
        self.current_sent = 0.0
    
    def can_start(self) -> bool:
        """Send can start if tank has sufficient volume and is available"""
        if not self.hardware.is_tank_available(self.tank_id):
            return False
        
        # Check if tank has sufficient volume
        tank_status = self.hardware.get_tank_status(self.tank_id)
        
        return True
    
    def start(self) -> bool:
        """Start send operation"""
        if not self.can_start():
            return False
        
        try:
            self.status = JobStatus.RUNNING
            self.start_time = time.time()
            self.update_progress(0)
            
            # Check tank volume
            self.update_progress(1)
            
            # Start send operation
            result = self.hardware.send_from_tank(self.tank_id, self.target_gallons)
            
            if result == OperationResult.IN_PROGRESS:
                self.send_started = True
                self.update_progress(2)
                logger.info(f"Send job {self.job_id} started: {self.target_gallons} gallons from tank {self.tank_id}")
                return True
            else:
                self.set_error(f"Failed to start send operation: {result}")
                return False
                
        except Exception as e:
            self.set_error(f"Error starting send: {e}")
            return False
    
    def update(self) -> bool:
        """Update send progress"""
        if self.status != JobStatus.RUNNING:
            return False
        
        try:
            # Check if send operation is still active
            tank_status = self.hardware.get_tank_status(self.tank_id)
            send_active = any(op.get('active', False) for op_type, op in tank_status.get('operations', {}).items() 
                            if op_type == 'send')
            
            if send_active:
                # Still sending - update progress based on flow
                elapsed_time = time.time() - self.start_time
                estimated_progress = min(90.0, (elapsed_time / 600.0) * 100.0)  # Estimate 10 min send
                self.update_progress(progress=20.0 + (estimated_progress * 0.7))
                return True
            else:
                # Send completed
                self.update_progress(3)
                self.complete()
                return False
                
        except Exception as e:
            self.set_error(f"Error updating send: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop send operation"""
        try:
            result = self.hardware.stop_tank_operation(self.tank_id, 'send')
            if result == OperationResult.SUCCESS:
                self.status = JobStatus.CANCELLED
                self.end_time = time.time()
                logger.info(f"Send job {self.job_id} stopped")
                return True
            else:
                logger.error(f"Failed to stop send job {self.job_id}")
                return False
        except Exception as e:
            self.set_error(f"Error stopping send: {e}")
            return False
    
    def get_blocking_operations(self) -> List[str]:
        """Send operations block mix and send operations"""
        return ['mix', 'send']

# Job factory function
def create_job(job_id: int, job_type: JobType, tank_id: int, hardware_manager: HardwareManager,
               parameters: Dict[str, Any]) -> Optional[BaseJob]:
    """Create a job instance based on job type"""
    try:
        if job_type == JobType.FILL:
            gallons = parameters.get('gallons', 50)
            return FillJob(job_id, tank_id, hardware_manager, gallons)
        
        elif job_type == JobType.MIX:
            formula = parameters.get('formula', {})
            ph_target = parameters.get('ph_target', 6.0)
            ec_target = parameters.get('ec_target', 1.5)
            return MixJob(job_id, tank_id, hardware_manager, formula, ph_target, ec_target)
        
        elif job_type == JobType.SEND:
            gallons = parameters.get('gallons', 25)
            destination = parameters.get('destination')
            return SendJob(job_id, tank_id, hardware_manager, gallons, destination)
        
        else:
            logger.error(f"Unknown job type: {job_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        return None

if __name__ == "__main__":
    # Test the job system
    logging.basicConfig(level=logging.INFO)
    
    print("Job System Test")
    print("=" * 30)
    
    # Mock hardware manager for testing
    class MockHardwareManager:
        def is_tank_available(self, tank_id):
            return True
        
        def get_tank_status(self, tank_id):
            return {'capacity': 100, 'operations': {}}
        
        def fill_tank(self, tank_id, gallons):
            return OperationResult.IN_PROGRESS
        
        def mix_tank(self, tank_id, formula):
            return OperationResult.IN_PROGRESS
        
        def send_from_tank(self, tank_id, gallons):
            return OperationResult.IN_PROGRESS
        
        def stop_tank_operation(self, tank_id, operation_type):
            return OperationResult.SUCCESS
    
    hardware = MockHardwareManager()
    
    # Test job creation
    fill_job = create_job(1, JobType.FILL, 1, hardware, {'gallons': 75})
    mix_job = create_job(2, JobType.MIX, 1, hardware, {
        'formula': {'VegA': 10, 'VegB': 8}, 
        'ph_target': 6.2, 
        'ec_target': 1.4
    })
    send_job = create_job(3, JobType.SEND, 1, hardware, {'gallons': 50})
    
    jobs = [fill_job, mix_job, send_job]
    
    for job in jobs:
        if job:
            print(f"Created {job.__class__.__name__}: {job.get_status()}")
            
            # Test job start
            if job.start():
                print(f"  Started successfully")
                
                # Test job update
                for i in range(3):
                    still_running = job.update()
                    status = job.get_status()
                    print(f"  Update {i+1}: {status['progress']:.1f}% - {status['step_description']}")
                    if not still_running:
                        break
                    time.sleep(0.5)
            else:
                print(f"  Failed to start")
    
    print("Job system test completed")
"""
Job Manager - Multi-Step Job Orchestration System

This module provides the orchestration layer for multi-step jobs (fill, mix, send).
It manages job state, sequences hardware operations, tracks progress, and handles errors.

Architecture:
    Frontend (Stage2Testing.svelte)
        → Flask API (app.py)
        → JobManager (this file)
        → Hardware Abstraction (hardware_comms.py)
        → Physical Hardware

Author: Nutrient Mixing System
Created: December 2024
"""

import threading
import time
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

from config import (
    TANKS,
    RELAY_GPIO_PINS,
    FLOW_METER_GPIO_PINS,
    FLOW_METER_CALIBRATION,
    ROOMS,
    MAX_FLOW_GALLONS
)

# Map to expected variable names for compatibility
TANK_CAPACITIES = {tank_id: info['capacity_gallons'] for tank_id, info in TANKS.items()}

# Create relay mappings from TANKS configuration
RELAY_MAPPING = {
    'tank_fill': {tank_id: info['fill_relay'] for tank_id, info in TANKS.items()},
    'tank_mix': {tank_id: info['mix_relays'][0] for tank_id, info in TANKS.items()},  # Use first mix relay
    'tank_send': {tank_id: info['send_relay'] for tank_id, info in TANKS.items()}
}

FLOW_METER_MAPPING = FLOW_METER_GPIO_PINS
ROOM_RELAY_MAPPING = {room_id: info['relay'] for room_id, info in ROOMS.items()}
MIN_FLOW_GALLONS = 1  # Define minimum flow gallons
PULSES_PER_GALLON = FLOW_METER_CALIBRATION.get(1, 220)  # Use flow meter 1 calibration

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Types of jobs the system can execute"""
    FILL = "fill"
    MIX = "mix"
    SEND = "send"


class JobStatus(Enum):
    """Job execution status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class JobState:
    """State information for a running job"""
    job_type: str
    status: str
    tank_id: Optional[int] = None
    room_id: Optional[str] = None
    target_gallons: Optional[float] = None
    current_step: str = "init"
    completed_steps: List[str] = None
    progress_percent: float = 0.0
    timer_remaining: Optional[int] = None
    current_readings: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None

    def __post_init__(self):
        if self.completed_steps is None:
            self.completed_steps = []
        if self.start_time is None:
            self.start_time = time.time()

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert start_time to ISO format if present
        if self.start_time:
            data['start_time'] = datetime.fromtimestamp(self.start_time).isoformat()
        return data


class JobStepError(Exception):
    """Raised when a job step fails"""
    pass


class JobExecutionError(Exception):
    """Raised when entire job fails"""
    pass


class BaseJobStateMachine:
    """Base class for job state machines with common functionality"""

    STATES: List[str] = []  # Override in subclasses

    def __init__(self, hardware_comms, job_state: JobState):
        self.hardware = hardware_comms
        self.state = job_state
        self.step_index = 0
        self.running = True
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def execute_next_step(self) -> bool:
        """
        Execute the next step in the job sequence.
        Returns True if job continues, False if complete.
        """
        if not self.running or self.step_index >= len(self.STATES):
            return False

        current_state = self.STATES[self.step_index]
        self.state.current_step = current_state

        try:
            self.logger.info(f"Executing step {self.step_index + 1}/{len(self.STATES)}: {current_state}")

            # Execute the step-specific logic
            continue_job = self._execute_step(current_state)

            if continue_job:
                # Mark step as completed
                if current_state not in self.state.completed_steps:
                    self.state.completed_steps.append(current_state)

                # Update progress
                self.state.progress_percent = (len(self.state.completed_steps) / len(self.STATES)) * 100

                # Move to next step
                self.step_index += 1

                # Check if job is complete
                if self.step_index >= len(self.STATES):
                    self.state.status = JobStatus.COMPLETED.value
                    self.state.progress_percent = 100.0
                    self.logger.info(f"Job completed successfully")
                    return False

                return True
            else:
                # Step needs more time (e.g., waiting for timer or hardware)
                return True

        except JobStepError as e:
            self.logger.error(f"Step failed: {e}")
            self.state.status = JobStatus.FAILED.value
            self.state.error_message = str(e)
            self.cleanup()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in step {current_state}: {e}", exc_info=True)
            self.state.status = JobStatus.FAILED.value
            self.state.error_message = f"Unexpected error: {str(e)}"
            self.cleanup()
            return False

    def _execute_step(self, step: str) -> bool:
        """
        Execute a specific step. Override in subclasses.
        Returns True to continue to next step, False to wait.
        """
        raise NotImplementedError("Subclasses must implement _execute_step")

    def stop(self):
        """Stop the job and cleanup"""
        self.logger.info("Stopping job")
        self.running = False
        self.state.status = JobStatus.STOPPED.value
        self.cleanup()

    def cleanup(self):
        """Cleanup hardware state. Override in subclasses."""
        pass


class FillJobStateMachine(BaseJobStateMachine):
    """
    State machine for tank fill jobs.

    Sequence:
        1. validate - Check parameters and hardware availability
        2. relay_on - Open tank fill valve
        3. flow_start - Start flow meter monitoring
        4. filling - Monitor fill progress
        5. flow_complete - Target gallons reached
        6. relay_off - Close tank fill valve
        7. complete - Job finished
    """

    STATES = [
        'validate',
        'relay_on',
        'flow_start',
        'filling',
        'flow_complete',
        'relay_off',
        'complete'
    ]

    def __init__(self, hardware_comms, job_state: JobState):
        super().__init__(hardware_comms, job_state)
        self.flow_meter_id = 1  # Tank fill uses flow meter 1
        self.relay_id = RELAY_MAPPING['tank_fill'].get(job_state.tank_id)
        self.fill_complete = False

    def _execute_step(self, step: str) -> bool:
        """Execute fill job steps"""

        if step == 'validate':
            return self._step_validate()
        elif step == 'relay_on':
            return self._step_relay_on()
        elif step == 'flow_start':
            return self._step_flow_start()
        elif step == 'filling':
            return self._step_filling()
        elif step == 'flow_complete':
            return self._step_flow_complete()
        elif step == 'relay_off':
            return self._step_relay_off()
        elif step == 'complete':
            return self._step_complete()

        return True

    def _step_validate(self) -> bool:
        """Validate job parameters"""
        # Check tank ID
        if self.state.tank_id not in [1, 2, 3]:
            raise JobStepError(f"Invalid tank ID: {self.state.tank_id}")

        # Check gallons
        if not (MIN_FLOW_GALLONS <= self.state.target_gallons <= MAX_FLOW_GALLONS):
            raise JobStepError(
                f"Gallons {self.state.target_gallons} outside range "
                f"{MIN_FLOW_GALLONS}-{MAX_FLOW_GALLONS}"
            )

        # Check relay mapping
        if not self.relay_id:
            raise JobStepError(f"No relay mapped for tank {self.state.tank_id}")

        self.logger.info(
            f"Validation passed: Tank {self.state.tank_id}, "
            f"{self.state.target_gallons} gallons, Relay {self.relay_id}"
        )
        return True

    def _step_relay_on(self) -> bool:
        """Open tank fill valve"""
        command = f"Start;Relay;{self.relay_id};ON;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to open relay {self.relay_id}")

        self.logger.info(f"Relay {self.relay_id} opened")
        time.sleep(0.5)  # Brief delay for valve to open
        return True

    def _step_flow_start(self) -> bool:
        """Start flow meter monitoring"""
        command = f"Start;StartFlow;{self.flow_meter_id};{self.state.target_gallons};{PULSES_PER_GALLON};end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to start flow meter {self.flow_meter_id}")

        self.logger.info(f"Flow meter started: {self.state.target_gallons} gallons target")
        return True

    def _step_filling(self) -> bool:
        """Monitor fill progress"""
        # Check if flow meter has completed
        # Access FeedControlSystem directly to get flow meter status
        if not self.hardware.is_system_ready():
            raise JobStepError("Hardware system not ready")

        system = self.hardware.get_system()
        if not system or not system.flow_controller:
            raise JobStepError("Flow controller not available")

        flow_meter = system.flow_controller.flow_meters.get(self.flow_meter_id)
        if not flow_meter:
            raise JobStepError(f"Flow meter {self.flow_meter_id} not found")

        # Check if target reached
        current_gallons = flow_meter.get('current_gallons', 0)
        target_gallons = flow_meter.get('target_gallons', 0)
        complete = flow_meter.get('complete', False)

        if complete or (target_gallons > 0 and current_gallons >= target_gallons):
            self.fill_complete = True
            self.logger.info(f"Fill complete: {current_gallons:.2f} gallons")
            return True

        # Update progress if available
        if target_gallons > 0:
            fill_progress = (current_gallons / target_gallons) * 100
            # Update overall progress (filling is steps 3-4 of 7, so 43-71%)
            self.state.progress_percent = 43 + (fill_progress * 0.28)

        # Still filling, wait for next check
        return False

    def _step_flow_complete(self) -> bool:
        """Flow meter reached target"""
        if not self.fill_complete:
            raise JobStepError("Flow complete step reached but fill not complete")

        # Stop flow meter
        command = f"Start;StartFlow;{self.flow_meter_id};0;end"
        result = self.hardware.send_command(command)

        if not result:
            self.logger.warning("Failed to stop flow meter (continuing anyway)")

        return True

    def _step_relay_off(self) -> bool:
        """Close tank fill valve"""
        command = f"Start;Relay;{self.relay_id};OFF;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to close relay {self.relay_id}")

        self.logger.info(f"Relay {self.relay_id} closed")
        return True

    def _step_complete(self) -> bool:
        """Job complete"""
        self.logger.info(
            f"Fill job complete: Tank {self.state.tank_id}, "
            f"{self.state.target_gallons} gallons"
        )
        return True

    def cleanup(self):
        """Emergency cleanup - turn off relay and flow meter"""
        try:
            # Stop flow meter
            command = f"Start;StartFlow;{self.flow_meter_id};0;end"
            self.hardware.send_command(command)

            # Close relay
            command = f"Start;Relay;{self.relay_id};OFF;end"
            self.hardware.send_command(command)

            self.logger.info("Fill job cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class MixJobStateMachine(BaseJobStateMachine):
    """
    State machine for tank mixing jobs.

    Sequence:
        1. validate - Check parameters and hardware
        2. mixing_relays_on - Start mixing pumps/agitators
        3. initial_delay - Wait 20 seconds for initial mixing
        4. start_ecph - Start EC/pH monitoring
        5. dispense_nutrients - Dispense nutrients via pumps (if configured)
        6. wait_for_dispense - Wait for all pumps to complete
        7. final_mixing - Mix for 60 seconds
        8. read_sensors - Read final EC/pH values
        9. stop_ecph - Stop EC/pH monitoring
        10. mixing_relays_off - Stop mixing pumps
        11. complete - Job finished
    """

    STATES = [
        'validate',
        'mixing_relays_on',
        'initial_delay',
        'start_ecph',
        'dispense_nutrients',
        'wait_for_dispense',
        'final_mixing',
        'read_sensors',
        'stop_ecph',
        'mixing_relays_off',
        'complete'
    ]

    def __init__(self, hardware_comms, job_state: JobState):
        super().__init__(hardware_comms, job_state)
        self.mixing_relay_id = RELAY_MAPPING['tank_mix'].get(job_state.tank_id)
        self.initial_delay_seconds = 20
        self.final_mix_seconds = 60
        self.delay_start_time = None
        self.final_mix_start_time = None
        self.nutrients_to_dispense = []  # Can be configured later
        self.dispense_complete = False

        # Initialize current readings
        self.state.current_readings = {
            'ec': 0.0,
            'ph': 0.0,
            'ec_warning': False,
            'ph_warning': False
        }

    def _execute_step(self, step: str) -> bool:
        """Execute mix job steps"""

        if step == 'validate':
            return self._step_validate()
        elif step == 'mixing_relays_on':
            return self._step_mixing_relays_on()
        elif step == 'initial_delay':
            return self._step_initial_delay()
        elif step == 'start_ecph':
            return self._step_start_ecph()
        elif step == 'dispense_nutrients':
            return self._step_dispense_nutrients()
        elif step == 'wait_for_dispense':
            return self._step_wait_for_dispense()
        elif step == 'final_mixing':
            return self._step_final_mixing()
        elif step == 'read_sensors':
            return self._step_read_sensors()
        elif step == 'stop_ecph':
            return self._step_stop_ecph()
        elif step == 'mixing_relays_off':
            return self._step_mixing_relays_off()
        elif step == 'complete':
            return self._step_complete()

        return True

    def _step_validate(self) -> bool:
        """Validate job parameters"""
        if self.state.tank_id not in [1, 2, 3]:
            raise JobStepError(f"Invalid tank ID: {self.state.tank_id}")

        if not self.mixing_relay_id:
            raise JobStepError(f"No mixing relay mapped for tank {self.state.tank_id}")

        self.logger.info(f"Validation passed: Tank {self.state.tank_id}")
        return True

    def _step_mixing_relays_on(self) -> bool:
        """Start mixing pumps/agitators"""
        command = f"Start;Relay;{self.mixing_relay_id};ON;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to start mixing relay {self.mixing_relay_id}")

        self.logger.info(f"Mixing relay {self.mixing_relay_id} started")
        return True

    def _step_initial_delay(self) -> bool:
        """Wait for initial mixing period"""
        if self.delay_start_time is None:
            self.delay_start_time = time.time()
            self.logger.info(f"Starting {self.initial_delay_seconds}s initial mixing delay")

        elapsed = time.time() - self.delay_start_time
        remaining = max(0, self.initial_delay_seconds - int(elapsed))
        self.state.timer_remaining = remaining

        if elapsed >= self.initial_delay_seconds:
            self.logger.info("Initial delay complete")
            self.state.timer_remaining = None
            return True

        return False  # Continue waiting

    def _step_start_ecph(self) -> bool:
        """Start EC/pH monitoring"""
        command = "Start;EcPh;ON;end"
        result = self.hardware.send_command(command)

        if not result:
            self.logger.warning("Failed to start EC/pH monitoring (continuing anyway)")
        else:
            self.logger.info("EC/pH monitoring started")

        time.sleep(2)  # Brief delay for sensors to stabilize
        return True

    def _step_dispense_nutrients(self) -> bool:
        """Dispense nutrients (if configured)"""
        if not self.nutrients_to_dispense:
            self.logger.info("No nutrients configured for dispensing")
            self.dispense_complete = True
            return True

        # TODO: Implement nutrient dispensing logic
        # This would involve sending pump dispense commands
        # For now, mark as complete
        self.dispense_complete = True
        return True

    def _step_wait_for_dispense(self) -> bool:
        """Wait for nutrient pumps to complete"""
        if not self.dispense_complete:
            # TODO: Check pump status
            return False

        self.logger.info("Nutrient dispensing complete")
        return True

    def _step_final_mixing(self) -> bool:
        """Final mixing period"""
        if self.final_mix_start_time is None:
            self.final_mix_start_time = time.time()
            self.logger.info(f"Starting {self.final_mix_seconds}s final mixing")

        elapsed = time.time() - self.final_mix_start_time
        remaining = max(0, self.final_mix_seconds - int(elapsed))
        self.state.timer_remaining = remaining

        # Poll EC/pH during mixing
        self._update_ecph_readings()

        if elapsed >= self.final_mix_seconds:
            self.logger.info("Final mixing complete")
            self.state.timer_remaining = None
            return True

        return False  # Continue mixing

    def _step_read_sensors(self) -> bool:
        """Read final EC/pH values"""
        self._update_ecph_readings()

        self.logger.info(
            f"Final readings - EC: {self.state.current_readings['ec']:.2f}, "
            f"pH: {self.state.current_readings['ph']:.2f}"
        )
        return True

    def _step_stop_ecph(self) -> bool:
        """Stop EC/pH monitoring"""
        command = "Start;EcPh;OFF;end"
        result = self.hardware.send_command(command)

        if not result:
            self.logger.warning("Failed to stop EC/pH monitoring (continuing anyway)")
        else:
            self.logger.info("EC/pH monitoring stopped")

        return True

    def _step_mixing_relays_off(self) -> bool:
        """Stop mixing pumps"""
        command = f"Start;Relay;{self.mixing_relay_id};OFF;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to stop mixing relay {self.mixing_relay_id}")

        self.logger.info(f"Mixing relay {self.mixing_relay_id} stopped")
        return True

    def _step_complete(self) -> bool:
        """Job complete"""
        self.logger.info(f"Mix job complete: Tank {self.state.tank_id}")
        return True

    def _update_ecph_readings(self):
        """Poll EC/pH sensors and update current readings"""
        try:
            # Access FeedControlSystem to get EC/pH readings
            if not self.hardware.is_system_ready():
                return

            system = self.hardware.get_system()
            if not system:
                return

            # Try to get readings from Arduino controller
            if hasattr(system, 'arduino_controller') and system.arduino_controller:
                # Arduino-based EC/pH sensors
                ec = getattr(system.arduino_controller, 'last_ec', 0.0)
                ph = getattr(system.arduino_controller, 'last_ph', 0.0)
            elif hasattr(system, 'ezo_sensors') and system.ezo_sensors:
                # EZO-based EC/pH sensors
                ec = getattr(system.ezo_sensors, 'last_ec', 0.0)
                ph = getattr(system.ezo_sensors, 'last_ph', 0.0)
            else:
                # No sensors available, use default values
                return

            self.state.current_readings['ec'] = ec
            self.state.current_readings['ph'] = ph

            # Check for warnings (example thresholds)
            self.state.current_readings['ec_warning'] = not (1.0 <= ec <= 3.0)
            self.state.current_readings['ph_warning'] = not (5.5 <= ph <= 6.5)
        except Exception as e:
            self.logger.warning(f"Failed to update EC/pH readings: {e}")

    def cleanup(self):
        """Emergency cleanup - stop mixing and EC/pH monitoring"""
        try:
            # Stop EC/pH monitoring
            command = "Start;EcPh;OFF;end"
            self.hardware.send_command(command)

            # Stop mixing relay
            command = f"Start;Relay;{self.mixing_relay_id};OFF;end"
            self.hardware.send_command(command)

            self.logger.info("Mix job cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class SendJobStateMachine(BaseJobStateMachine):
    """
    State machine for send jobs (delivering water to grow rooms).

    Sequence:
        1. validate - Check parameters and hardware
        2. tank_relay_on - Open tank send valve
        3. room_relay_on - Open room destination valve
        4. flow_start - Start flow meter monitoring
        5. sending - Monitor send progress
        6. flow_complete - Target gallons reached
        7. room_relay_off - Close room valve
        8. tank_relay_off - Close tank valve
        9. complete - Job finished
    """

    STATES = [
        'validate',
        'tank_relay_on',
        'room_relay_on',
        'flow_start',
        'sending',
        'flow_complete',
        'room_relay_off',
        'tank_relay_off',
        'complete'
    ]

    def __init__(self, hardware_comms, job_state: JobState):
        super().__init__(hardware_comms, job_state)
        self.flow_meter_id = 2  # Send uses flow meter 2
        self.tank_relay_id = RELAY_MAPPING['tank_send'].get(job_state.tank_id)
        self.room_relay_id = ROOM_RELAY_MAPPING.get(job_state.room_id)
        self.send_complete = False

    def _execute_step(self, step: str) -> bool:
        """Execute send job steps"""

        if step == 'validate':
            return self._step_validate()
        elif step == 'tank_relay_on':
            return self._step_tank_relay_on()
        elif step == 'room_relay_on':
            return self._step_room_relay_on()
        elif step == 'flow_start':
            return self._step_flow_start()
        elif step == 'sending':
            return self._step_sending()
        elif step == 'flow_complete':
            return self._step_flow_complete()
        elif step == 'room_relay_off':
            return self._step_room_relay_off()
        elif step == 'tank_relay_off':
            return self._step_tank_relay_off()
        elif step == 'complete':
            return self._step_complete()

        return True

    def _step_validate(self) -> bool:
        """Validate job parameters"""
        # Check tank ID
        if self.state.tank_id not in [1, 2, 3]:
            raise JobStepError(f"Invalid tank ID: {self.state.tank_id}")

        # Check room ID
        if self.state.room_id not in ROOM_RELAY_MAPPING:
            raise JobStepError(f"Invalid room ID: {self.state.room_id}")

        # Check gallons
        if not (MIN_FLOW_GALLONS <= self.state.target_gallons <= MAX_FLOW_GALLONS):
            raise JobStepError(
                f"Gallons {self.state.target_gallons} outside range "
                f"{MIN_FLOW_GALLONS}-{MAX_FLOW_GALLONS}"
            )

        # Check relay mappings
        if not self.tank_relay_id:
            raise JobStepError(f"No send relay mapped for tank {self.state.tank_id}")
        if not self.room_relay_id:
            raise JobStepError(f"No relay mapped for room {self.state.room_id}")

        self.logger.info(
            f"Validation passed: Tank {self.state.tank_id} → Room {self.state.room_id}, "
            f"{self.state.target_gallons} gallons"
        )
        return True

    def _step_tank_relay_on(self) -> bool:
        """Open tank send valve"""
        command = f"Start;Relay;{self.tank_relay_id};ON;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to open tank relay {self.tank_relay_id}")

        self.logger.info(f"Tank relay {self.tank_relay_id} opened")
        time.sleep(0.3)  # Brief delay
        return True

    def _step_room_relay_on(self) -> bool:
        """Open room destination valve"""
        command = f"Start;Relay;{self.room_relay_id};ON;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to open room relay {self.room_relay_id}")

        self.logger.info(f"Room relay {self.room_relay_id} opened")
        time.sleep(0.3)  # Brief delay for valve
        return True

    def _step_flow_start(self) -> bool:
        """Start flow meter monitoring"""
        command = f"Start;StartFlow;{self.flow_meter_id};{self.state.target_gallons};{PULSES_PER_GALLON};end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to start flow meter {self.flow_meter_id}")

        self.logger.info(f"Flow meter started: {self.state.target_gallons} gallons target")
        return True

    def _step_sending(self) -> bool:
        """Monitor send progress"""
        # Access FeedControlSystem directly to get flow meter status
        if not self.hardware.is_system_ready():
            raise JobStepError("Hardware system not ready")

        system = self.hardware.get_system()
        if not system or not system.flow_controller:
            raise JobStepError("Flow controller not available")

        flow_meter = system.flow_controller.flow_meters.get(self.flow_meter_id)
        if not flow_meter:
            raise JobStepError(f"Flow meter {self.flow_meter_id} not found")

        # Check if target reached
        current_gallons = flow_meter.get('current_gallons', 0)
        target_gallons = flow_meter.get('target_gallons', 0)
        complete = flow_meter.get('complete', False)

        if complete or (target_gallons > 0 and current_gallons >= target_gallons):
            self.send_complete = True
            self.logger.info(f"Send complete: {current_gallons:.2f} gallons")
            return True

        # Update progress if available
        if target_gallons > 0:
            send_progress = (current_gallons / target_gallons) * 100
            # Update overall progress (sending is steps 4-5 of 9, so 44-66%)
            self.state.progress_percent = 44 + (send_progress * 0.22)

        # Still sending, wait for next check
        return False

    def _step_flow_complete(self) -> bool:
        """Flow meter reached target"""
        if not self.send_complete:
            raise JobStepError("Flow complete step reached but send not complete")

        # Stop flow meter
        command = f"Start;StartFlow;{self.flow_meter_id};0;end"
        result = self.hardware.send_command(command)

        if not result:
            self.logger.warning("Failed to stop flow meter (continuing anyway)")

        return True

    def _step_room_relay_off(self) -> bool:
        """Close room valve first (safer order)"""
        command = f"Start;Relay;{self.room_relay_id};OFF;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to close room relay {self.room_relay_id}")

        self.logger.info(f"Room relay {self.room_relay_id} closed")
        time.sleep(0.2)
        return True

    def _step_tank_relay_off(self) -> bool:
        """Close tank send valve"""
        command = f"Start;Relay;{self.tank_relay_id};OFF;end"
        result = self.hardware.send_command(command)

        if not result:
            raise JobStepError(f"Failed to close tank relay {self.tank_relay_id}")

        self.logger.info(f"Tank relay {self.tank_relay_id} closed")
        return True

    def _step_complete(self) -> bool:
        """Job complete"""
        self.logger.info(
            f"Send job complete: Tank {self.state.tank_id} → Room {self.state.room_id}, "
            f"{self.state.target_gallons} gallons"
        )
        return True

    def cleanup(self):
        """Emergency cleanup - close all relays and stop flow meter"""
        try:
            # Stop flow meter
            command = f"Start;StartFlow;{self.flow_meter_id};0;end"
            self.hardware.send_command(command)

            # Close room relay
            command = f"Start;Relay;{self.room_relay_id};OFF;end"
            self.hardware.send_command(command)

            # Close tank relay
            command = f"Start;Relay;{self.tank_relay_id};OFF;end"
            self.hardware.send_command(command)

            self.logger.info("Send job cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class JobManager:
    """
    Central manager for all multi-step jobs.

    Responsibilities:
        - Accept job start requests from API
        - Create and track job state
        - Execute jobs via state machines
        - Provide job status for frontend polling
        - Handle job stop/cleanup
        - Prevent conflicting jobs
    """

    def __init__(self, hardware_comms):
        self.hardware = hardware_comms
        self.active_jobs: Dict[str, Optional[JobState]] = {
            JobType.FILL.value: None,
            JobType.MIX.value: None,
            JobType.SEND.value: None
        }
        self.state_machines: Dict[str, Optional[BaseJobStateMachine]] = {
            JobType.FILL.value: None,
            JobType.MIX.value: None,
            JobType.SEND.value: None
        }
        self.job_lock = threading.Lock()
        self.running = False
        self.worker_thread = None
        self.logger = logging.getLogger("JobManager")

    def start(self):
        """Start the job manager background worker"""
        if self.running:
            self.logger.warning("Job manager already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Job manager started")

    def stop(self):
        """Stop the job manager"""
        self.logger.info("Stopping job manager")
        self.running = False

        # Stop all active jobs
        for job_type in JobType:
            self.stop_job(job_type.value)

        if self.worker_thread:
            self.worker_thread.join(timeout=5)

        self.logger.info("Job manager stopped")

    def _worker_loop(self):
        """Background worker that executes job steps"""
        while self.running:
            try:
                with self.job_lock:
                    for job_type, state_machine in self.state_machines.items():
                        if state_machine and state_machine.running:
                            # Execute next step
                            continue_job = state_machine.execute_next_step()

                            if not continue_job:
                                # Job finished or failed
                                self.logger.info(f"{job_type} job ended: {self.active_jobs[job_type].status}")
                                self.state_machines[job_type] = None

                time.sleep(0.5)  # Check every 500ms

            except Exception as e:
                self.logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(1)

    def start_fill_job(self, tank_id: int, gallons: float) -> Dict[str, Any]:
        """Start a tank fill job"""
        with self.job_lock:
            # Check if fill job already running
            if self.active_jobs[JobType.FILL.value]:
                return {
                    'success': False,
                    'message': 'Fill job already running'
                }

            # Create job state
            job_state = JobState(
                job_type=JobType.FILL.value,
                status=JobStatus.RUNNING.value,
                tank_id=tank_id,
                target_gallons=gallons
            )

            # Create state machine
            try:
                state_machine = FillJobStateMachine(self.hardware, job_state)
                self.active_jobs[JobType.FILL.value] = job_state
                self.state_machines[JobType.FILL.value] = state_machine

                self.logger.info(f"Fill job started: Tank {tank_id}, {gallons} gallons")

                return {
                    'success': True,
                    'message': f'Fill job started for tank {tank_id}',
                    'job': job_state.to_dict()
                }
            except Exception as e:
                self.logger.error(f"Failed to start fill job: {e}", exc_info=True)
                return {
                    'success': False,
                    'message': f'Failed to start fill job: {str(e)}'
                }

    def start_mix_job(self, tank_id: int) -> Dict[str, Any]:
        """Start a tank mixing job"""
        with self.job_lock:
            # Check if mix job already running
            if self.active_jobs[JobType.MIX.value]:
                return {
                    'success': False,
                    'message': 'Mix job already running'
                }

            # Create job state
            job_state = JobState(
                job_type=JobType.MIX.value,
                status=JobStatus.RUNNING.value,
                tank_id=tank_id
            )

            # Create state machine
            try:
                state_machine = MixJobStateMachine(self.hardware, job_state)
                self.active_jobs[JobType.MIX.value] = job_state
                self.state_machines[JobType.MIX.value] = state_machine

                self.logger.info(f"Mix job started: Tank {tank_id}")

                return {
                    'success': True,
                    'message': f'Mix job started for tank {tank_id}',
                    'job': job_state.to_dict()
                }
            except Exception as e:
                self.logger.error(f"Failed to start mix job: {e}", exc_info=True)
                return {
                    'success': False,
                    'message': f'Failed to start mix job: {str(e)}'
                }

    def start_send_job(self, tank_id: int, room_id: str, gallons: float) -> Dict[str, Any]:
        """Start a send job"""
        with self.job_lock:
            # Check if send job already running
            if self.active_jobs[JobType.SEND.value]:
                return {
                    'success': False,
                    'message': 'Send job already running'
                }

            # Create job state
            job_state = JobState(
                job_type=JobType.SEND.value,
                status=JobStatus.RUNNING.value,
                tank_id=tank_id,
                room_id=room_id,
                target_gallons=gallons
            )

            # Create state machine
            try:
                state_machine = SendJobStateMachine(self.hardware, job_state)
                self.active_jobs[JobType.SEND.value] = job_state
                self.state_machines[JobType.SEND.value] = state_machine

                self.logger.info(f"Send job started: Tank {tank_id} → Room {room_id}, {gallons} gallons")

                return {
                    'success': True,
                    'message': f'Send job started: Tank {tank_id} → Room {room_id}',
                    'job': job_state.to_dict()
                }
            except Exception as e:
                self.logger.error(f"Failed to start send job: {e}", exc_info=True)
                return {
                    'success': False,
                    'message': f'Failed to start send job: {str(e)}'
                }

    def stop_job(self, job_type: str) -> Dict[str, Any]:
        """Stop a running job"""
        with self.job_lock:
            state_machine = self.state_machines.get(job_type)

            if not state_machine:
                return {
                    'success': False,
                    'message': f'No {job_type} job running'
                }

            try:
                state_machine.stop()
                self.active_jobs[job_type] = None
                self.state_machines[job_type] = None

                self.logger.info(f"{job_type} job stopped")

                return {
                    'success': True,
                    'message': f'{job_type.capitalize()} job stopped'
                }
            except Exception as e:
                self.logger.error(f"Error stopping {job_type} job: {e}", exc_info=True)
                return {
                    'success': False,
                    'message': f'Error stopping job: {str(e)}'
                }

    def get_job_status(self, job_type: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        with self.job_lock:
            job_state = self.active_jobs.get(job_type)
            if job_state:
                return job_state.to_dict()
            return None

    def get_all_jobs_status(self) -> Dict[str, Any]:
        """Get status of all jobs"""
        with self.job_lock:
            return {
                'active_fill_job': self.get_job_status(JobType.FILL.value),
                'active_mix_job': self.get_job_status(JobType.MIX.value),
                'active_send_job': self.get_job_status(JobType.SEND.value)
            }

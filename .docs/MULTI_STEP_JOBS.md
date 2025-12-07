# Multi-Step Job System Documentation

**Version**: 1.0
**Created**: December 2024
**Last Updated**: December 2024

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Job Types](#job-types)
4. [Job State Machine](#job-state-machine)
5. [API Endpoints](#api-endpoints)
6. [Frontend Integration](#frontend-integration)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Multi-Step Job System orchestrates complex hardware operations by chaining together individual hardware commands (relays, pumps, flow meters, sensors) into automated workflows. This system bridges the gap between Stage 1 (individual hardware testing) and Stage 2 (complete job workflows).

### Key Features

- **State Machine Architecture**: Each job type uses a dedicated state machine to manage step-by-step execution
- **Real-time Progress Tracking**: Frontend receives continuous updates on current step, completed steps, and progress percentage
- **Error Recovery**: Automatic hardware cleanup on failures with detailed error messages
- **Concurrent Prevention**: Resource locking prevents conflicting jobs from running simultaneously
- **Background Execution**: Jobs run in a dedicated background thread without blocking the API
- **Timer Support**: Mix jobs include timed steps (initial delay, final mixing period)
- **Sensor Integration**: Mix jobs continuously monitor EC/pH during execution

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Svelte 5)                      │
│                  Stage2Testing.svelte                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │ Fill Job UI  │  │ Mix Job UI   │  │ Send Job UI  │   │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│          │                  │                  │            │
└──────────┼──────────────────┼──────────────────┼────────────┘
           │                  │                  │
           │ POST /api/jobs/fill/start           │
           │ POST /api/jobs/mix/start            │
           │ POST /api/jobs/send/start           │
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask API (app.py)                       │
│              Job Endpoint Handlers                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Job Manager (job_manager.py)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Fill Job SM  │  │ Mix Job SM   │  │ Send Job SM  │     │
│  │ (7 steps)    │  │ (11 steps)   │  │ (9 steps)    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│              Background Worker Thread                        │
│         (Executes job steps every 500ms)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│          Hardware Abstraction (hardware_comms.py)           │
│   send_command() / get_flow_status() / get_ecph_readings()  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Physical Hardware                        │
│   Relays │ Pumps │ Flow Meters │ EC/pH Sensors              │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### System Components

#### 1. **JobManager** (`job_manager.py`)

The central orchestrator that manages all multi-step jobs.

**Responsibilities:**
- Accept job start requests from API endpoints
- Create and track job state for fill, mix, and send jobs
- Execute jobs via state machines in background thread
- Provide job status for frontend polling
- Handle job stop/cleanup requests
- Prevent conflicting jobs through resource locking

**Key Methods:**
```python
JobManager(hardware_comms)
├── start()                    # Start background worker thread
├── stop()                     # Stop manager and all jobs
├── start_fill_job(tank_id, gallons)
├── start_mix_job(tank_id)
├── start_send_job(tank_id, room_id, gallons)
├── stop_job(job_type)
├── get_job_status(job_type)
└── get_all_jobs_status()
```

#### 2. **State Machines** (`job_manager.py`)

Each job type has a dedicated state machine class:

- **FillJobStateMachine**: Tank fill operations (7 steps)
- **MixJobStateMachine**: Nutrient mixing operations (11 steps)
- **SendJobStateMachine**: Tank-to-room send operations (9 steps)

**Base State Machine Pattern:**
```python
BaseJobStateMachine
├── STATES[]                   # List of step names
├── execute_next_step()        # Execute current step
├── _execute_step(step)        # Step-specific logic (override)
├── stop()                     # Stop job execution
└── cleanup()                  # Hardware cleanup (override)
```

#### 3. **JobState** (`job_manager.py`)

Dataclass that holds the current state of a running job.

**Properties:**
```python
JobState
├── job_type: str              # 'fill', 'mix', or 'send'
├── status: str                # 'idle', 'running', 'completed', 'failed', 'stopped'
├── tank_id: int               # Tank being operated on
├── room_id: str               # Room destination (send jobs only)
├── target_gallons: float      # Target volume (fill/send jobs)
├── current_step: str          # Currently executing step
├── completed_steps: List[str] # Steps that have finished
├── progress_percent: float    # Overall job progress (0-100)
├── timer_remaining: int       # Countdown timer (mix jobs)
├── current_readings: dict     # EC/pH readings (mix jobs)
├── error_message: str         # Error details if failed
└── start_time: float          # Job start timestamp
```

---

## Job Types

### 1. Fill Job

**Purpose**: Fill a tank with water from the main water supply.

**Hardware Involved**:
- Tank fill relay (opens water valve)
- Flow meter 1 (measures water volume)

**Step Sequence** (7 steps):

```
┌──────────────┐
│  1. validate │ → Check tank_id, gallons, relay mapping
└──────┬───────┘
       ▼
┌──────────────┐
│ 2. relay_on  │ → Open tank fill valve
└──────┬───────┘
       ▼
┌──────────────┐
│ 3. flow_start│ → Start flow meter monitoring
└──────┬───────┘
       ▼
┌──────────────┐
│  4. filling  │ → Monitor flow progress (WAIT state)
└──────┬───────┘   Continuously checks if target reached
       ▼
┌──────────────┐
│5.flow_complete│ → Stop flow meter
└──────┬───────┘
       ▼
┌──────────────┐
│ 6. relay_off │ → Close tank fill valve
└──────┬───────┘
       ▼
┌──────────────┐
│  7. complete │ → Job finished successfully
└──────────────┘
```

**Hardware Commands**:
```python
# Step 2: relay_on
"Start;Relay;{relay_id};ON;end"

# Step 3: flow_start
"Start;StartFlow;1;{gallons};220;end"

# Step 4: filling (polls flow status)
get_flow_meter_status(1)

# Step 5: flow_complete
"Start;StartFlow;1;0;end"

# Step 6: relay_off
"Start;Relay;{relay_id};OFF;end"
```

**Typical Duration**: 1-10 minutes depending on gallons (e.g., 50 gallons ≈ 5 minutes)

**Frontend API Calls**:
```javascript
// Start fill job
POST /api/jobs/fill/start
Body: { tank_id: 1, gallons: 50 }

// Poll status (every 2 seconds)
GET /api/system/status
Response: { active_fill_job: { current_step, progress_percent, ... } }

// Stop job if needed
POST /api/jobs/fill/stop
```

---

### 2. Mix Job

**Purpose**: Mix nutrients in a tank with EC/pH monitoring.

**Hardware Involved**:
- Tank mixing relay (activates mixing pump/agitator)
- EC/pH sensors (via Arduino Uno or EZO I2C)
- Optional: Nutrient pumps (future enhancement)

**Step Sequence** (11 steps):

```
┌──────────────┐
│  1. validate │ → Check tank_id, relay mapping
└──────┬───────┘
       ▼
┌──────────────┐
│2.mixing_relays_on│ → Start mixing pump
└──────┬───────┘
       ▼
┌──────────────┐
│3.initial_delay│ → Wait 20 seconds (TIMER)
└──────┬───────┘
       ▼
┌──────────────┐
│ 4. start_ecph│ → Start EC/pH monitoring
└──────┬───────┘
       ▼
┌──────────────┐
│5.dispense_nutrients│ → Dispense nutrients (optional)
└──────┬───────┘
       ▼
┌──────────────┐
│6.wait_for_dispense│ → Wait for pumps to complete
└──────┬───────┘
       ▼
┌──────────────┐
│7.final_mixing│ → Mix for 60 seconds (TIMER)
└──────┬───────┘   Continuously polls EC/pH sensors
       ▼
┌──────────────┐
│8.read_sensors│ → Read final EC/pH values
└──────┬───────┘
       ▼
┌──────────────┐
│ 9. stop_ecph │ → Stop EC/pH monitoring
└──────┬───────┘
       ▼
┌──────────────┐
│10.mixing_relays_off│ → Stop mixing pump
└──────┬───────┘
       ▼
┌──────────────┐
│ 11. complete │ → Job finished successfully
└──────────────┘
```

**Hardware Commands**:
```python
# Step 2: mixing_relays_on
"Start;Relay;{mixing_relay_id};ON;end"

# Step 3: initial_delay (20 seconds)
# No hardware command - just timer

# Step 4: start_ecph
"Start;EcPh;ON;end"

# Step 7: final_mixing (60 seconds)
# Continuously calls get_ecph_readings()

# Step 8: read_sensors
get_ecph_readings()

# Step 9: stop_ecph
"Start;EcPh;OFF;end"

# Step 10: mixing_relays_off
"Start;Relay;{mixing_relay_id};OFF;end"
```

**Timer States**:
- **initial_delay**: 20 seconds (allows initial mixing before sensors start)
- **final_mixing**: 60 seconds (mixing with EC/pH monitoring)

**EC/pH Monitoring**:
During `final_mixing` step, the job continuously polls sensors and updates:
```python
current_readings = {
    'ec': 1.4,              # Electrical conductivity
    'ph': 6.2,              # pH level
    'ec_warning': False,    # True if EC outside 1.0-3.0 range
    'ph_warning': False     # True if pH outside 5.5-6.5 range
}
```

**Typical Duration**: ~2 minutes (20s + 60s + overhead)

**Frontend API Calls**:
```javascript
// Start mix job
POST /api/jobs/mix/start
Body: { tank_id: 1 }

// Poll status
GET /api/system/status
Response: {
  active_mix_job: {
    current_step: "final_mixing",
    timer_remaining: 45,
    current_readings: { ec: 1.4, ph: 6.2, ... }
  }
}

// Stop job
POST /api/jobs/mix/stop
```

---

### 3. Send Job

**Purpose**: Send water/nutrients from a tank to a grow room.

**Hardware Involved**:
- Tank send relay (opens tank outlet valve)
- Room destination relay (opens room inlet valve)
- Flow meter 2 (measures volume sent)

**Step Sequence** (9 steps):

```
┌──────────────┐
│  1. validate │ → Check tank_id, room_id, gallons, relays
└──────┬───────┘
       ▼
┌──────────────┐
│2.tank_relay_on│ → Open tank send valve
└──────┬───────┘
       ▼
┌──────────────┐
│3.room_relay_on│ → Open room destination valve
└──────┬───────┘
       ▼
┌──────────────┐
│ 4. flow_start│ → Start flow meter monitoring
└──────┬───────┘
       ▼
┌──────────────┐
│  5. sending  │ → Monitor send progress (WAIT state)
└──────┬───────┘
       ▼
┌──────────────┐
│6.flow_complete│ → Stop flow meter
└──────┬───────┘
       ▼
┌──────────────┐
│7.room_relay_off│ → Close room valve (safer order)
└──────┬───────┘
       ▼
┌──────────────┐
│8.tank_relay_off│ → Close tank valve
└──────┬───────┘
       ▼
┌──────────────┐
│  9. complete │ → Job finished successfully
└──────────────┘
```

**Hardware Commands**:
```python
# Step 2: tank_relay_on
"Start;Relay;{tank_relay_id};ON;end"

# Step 3: room_relay_on
"Start;Relay;{room_relay_id};ON;end"

# Step 4: flow_start
"Start;StartFlow;2;{gallons};220;end"

# Step 5: sending (polls flow status)
get_flow_meter_status(2)

# Step 6: flow_complete
"Start;StartFlow;2;0;end"

# Step 7: room_relay_off
"Start;Relay;{room_relay_id};OFF;end"

# Step 8: tank_relay_off
"Start;Relay;{tank_relay_id};OFF;end"
```

**Safety Note**: Room relay closes before tank relay to prevent backflow.

**Typical Duration**: 1-10 minutes depending on gallons

**Frontend API Calls**:
```javascript
// Start send job
POST /api/jobs/send/start
Body: { tank_id: 1, room_id: "room_1", gallons: 25 }

// Poll status
GET /api/system/status
Response: { active_send_job: { current_step, progress_percent, ... } }

// Stop job
POST /api/jobs/send/stop
```

---

## Job State Machine

### State Machine Execution Flow

Each state machine follows this execution pattern:

```python
# Background worker loop (runs every 500ms)
while running:
    for job_type in ['fill', 'mix', 'send']:
        if state_machine exists and is active:
            continue_job = state_machine.execute_next_step()

            if not continue_job:
                # Job finished or failed
                cleanup state machine
```

### Step Execution Logic

```python
def execute_next_step():
    current_state = STATES[step_index]
    job_state.current_step = current_state

    try:
        # Execute step-specific logic
        continue_to_next = _execute_step(current_state)

        if continue_to_next:
            # Step completed, move to next
            completed_steps.append(current_state)
            progress_percent = (completed_steps / total_steps) * 100
            step_index += 1

            if step_index >= len(STATES):
                # All steps complete
                status = 'completed'
                return False  # Job done

            return True  # Continue to next step
        else:
            # Step needs more time (e.g., timer, flow meter)
            return True  # Keep waiting

    except JobStepError:
        # Step failed
        status = 'failed'
        cleanup()
        return False  # Job aborted
```

### Step Return Values

Each `_execute_step()` returns:
- **`True`**: Step complete, proceed to next step
- **`False`**: Step in progress, keep waiting (e.g., filling, timer countdown)

### WAIT States

Some steps are "WAIT states" that don't complete until a condition is met:

**Fill/Send Job - `filling`/`sending` step:**
```python
def _step_filling(self):
    flow_status = get_flow_meter_status(flow_id)

    if flow_status.get('complete'):
        # Target reached, proceed to next step
        return True
    else:
        # Update progress and keep waiting
        current = flow_status.get('current_gallons')
        progress = (current / target_gallons) * 100
        self.state.progress_percent = base_progress + (progress * step_weight)
        return False  # Keep waiting
```

**Mix Job - `initial_delay`/`final_mixing` steps:**
```python
def _step_initial_delay(self):
    if delay_start_time is None:
        delay_start_time = time.time()

    elapsed = time.time() - delay_start_time
    remaining = max(0, delay_seconds - int(elapsed))
    self.state.timer_remaining = remaining

    if elapsed >= delay_seconds:
        # Timer complete, proceed
        return True
    else:
        # Keep waiting
        return False
```

---

## API Endpoints

### Fill Job Endpoints

#### `POST /api/jobs/fill/start`

Start a tank fill job.

**Request Body**:
```json
{
  "tank_id": 1,
  "gallons": 50.0
}
```

**Response**:
```json
{
  "success": true,
  "message": "Fill job started for tank 1",
  "job": {
    "job_type": "fill",
    "status": "running",
    "tank_id": 1,
    "target_gallons": 50.0,
    "current_step": "validate",
    "completed_steps": [],
    "progress_percent": 0.0,
    "start_time": "2024-12-07T10:30:00"
  }
}
```

**Error Responses**:
- `400`: Missing or invalid parameters
- `500`: Job manager not initialized or hardware error

#### `POST /api/jobs/fill/stop`

Stop the active fill job.

**Response**:
```json
{
  "success": true,
  "message": "Fill job stopped"
}
```

---

### Mix Job Endpoints

#### `POST /api/jobs/mix/start`

Start a tank mixing job.

**Request Body**:
```json
{
  "tank_id": 1
}
```

**Response**:
```json
{
  "success": true,
  "message": "Mix job started for tank 1",
  "job": {
    "job_type": "mix",
    "status": "running",
    "tank_id": 1,
    "current_step": "validate",
    "completed_steps": [],
    "progress_percent": 0.0,
    "timer_remaining": null,
    "current_readings": {
      "ec": 0.0,
      "ph": 0.0,
      "ec_warning": false,
      "ph_warning": false
    },
    "start_time": "2024-12-07T10:35:00"
  }
}
```

#### `POST /api/jobs/mix/stop`

Stop the active mix job.

---

### Send Job Endpoints

#### `POST /api/jobs/send/start`

Start a send job (tank to room).

**Request Body**:
```json
{
  "tank_id": 1,
  "room_id": "room_1",
  "gallons": 25.0
}
```

**Response**:
```json
{
  "success": true,
  "message": "Send job started: Tank 1 → Room room_1",
  "job": {
    "job_type": "send",
    "status": "running",
    "tank_id": 1,
    "room_id": "room_1",
    "target_gallons": 25.0,
    "current_step": "validate",
    "completed_steps": [],
    "progress_percent": 0.0,
    "start_time": "2024-12-07T10:40:00"
  }
}
```

#### `POST /api/jobs/send/stop`

Stop the active send job.

---

### Status Endpoint

#### `GET /api/system/status`

Get complete system status including active jobs.

**Response** (excerpt):
```json
{
  "success": true,
  "timestamp": "2024-12-07 10:45:30",
  "active_fill_job": {
    "job_type": "fill",
    "status": "running",
    "tank_id": 1,
    "target_gallons": 50.0,
    "current_step": "filling",
    "completed_steps": ["validate", "relay_on", "flow_start"],
    "progress_percent": 45.2
  },
  "active_mix_job": null,
  "active_send_job": null,
  "relays": [...],
  "pumps": [...],
  "flow_meters": [...]
}
```

#### `GET /api/jobs/status`

Get status of all jobs (dedicated endpoint).

**Response**:
```json
{
  "success": true,
  "active_fill_job": { ... },
  "active_mix_job": { ... },
  "active_send_job": { ... }
}
```

---

## Frontend Integration

### Stage 2 Testing Page Structure

The `Stage2Testing.svelte` page has three sections:

```svelte
<FillJobTesting bind:activeJob={activeFillJob} />
<MixJobTesting bind:activeJob={activeMixJob} />
<SendJobTesting bind:activeJob={activeSendJob} />
```

### Job Component Pattern

Each job component follows this pattern:

```svelte
<script>
  let { activeJob = $bindable(null) } = $props();

  let tankId = $state(1);
  let gallons = $state(50);

  // Poll system status every 2 seconds
  $effect(() => {
    const interval = setInterval(async () => {
      const response = await fetch('/api/system/status');
      const data = await response.json();
      activeJob = data.active_fill_job;  // Update from backend
    }, 2000);

    return () => clearInterval(interval);
  });

  async function startJob() {
    const response = await fetch('/api/jobs/fill/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tank_id: tankId, gallons })
    });
    const data = await response.json();
    if (data.success) {
      activeJob = data.job;
    }
  }

  async function stopJob() {
    await fetch('/api/jobs/fill/stop', { method: 'POST' });
    activeJob = null;
  }
</script>

<div class="job-card">
  <h3>Fill Job</h3>

  {#if !activeJob}
    <!-- Job configuration UI -->
    <input bind:value={tankId} />
    <input bind:value={gallons} />
    <button onclick={startJob}>Start Fill</button>
  {:else}
    <!-- Job progress UI -->
    <p>Status: {activeJob.status}</p>
    <p>Step: {activeJob.current_step}</p>
    <progress value={activeJob.progress_percent} max="100" />
    <p>{activeJob.progress_percent.toFixed(1)}%</p>
    <button onclick={stopJob}>Stop</button>
  {/if}
</div>
```

### Progress Calculation

The frontend can calculate progress in multiple ways:

**Step-based progress**:
```javascript
const totalSteps = 7;  // For fill job
const progress = (activeJob.completed_steps.length / totalSteps) * 100;
```

**Backend-calculated progress**:
```javascript
const progress = activeJob.progress_percent;  // Already calculated by state machine
```

### Step Visualization

Display step progress with visual indicators:

```svelte
{#each steps as step, index}
  <div class="step"
       class:completed={activeJob.completed_steps.includes(step.id)}
       class:current={activeJob.current_step === step.id}
       class:pending={!activeJob.completed_steps.includes(step.id) && activeJob.current_step !== step.id}>
    <span class="step-number">{index + 1}</span>
    <span class="step-name">{step.name}</span>
    {#if activeJob.completed_steps.includes(step.id)}
      <CheckIcon />
    {:else if activeJob.current_step === step.id}
      <LoadingSpinner />
    {/if}
  </div>
{/each}
```

### Timer Display

For mix jobs, show countdown timers:

```svelte
{#if activeJob?.timer_remaining !== null}
  <div class="timer">
    <Clock />
    <span>{activeJob.timer_remaining}s remaining</span>
  </div>
{/if}
```

### EC/pH Display

For mix jobs, show real-time sensor readings:

```svelte
{#if activeJob?.current_readings}
  <div class="sensor-readings">
    <div class="reading" class:warning={activeJob.current_readings.ec_warning}>
      <span>EC:</span>
      <span>{activeJob.current_readings.ec.toFixed(2)}</span>
    </div>
    <div class="reading" class:warning={activeJob.current_readings.ph_warning}>
      <span>pH:</span>
      <span>{activeJob.current_readings.ph.toFixed(2)}</span>
    </div>
  </div>
{/if}
```

---

## Error Handling

### Error Types

#### 1. Validation Errors

Occur during the `validate` step before any hardware is touched.

**Examples**:
- Invalid tank ID
- Gallons outside valid range
- No relay mapped for tank
- Invalid room ID

**Response**:
```json
{
  "success": false,
  "message": "Failed to start fill job: Invalid tank ID: 5"
}
```

**Recovery**: User corrects parameters and tries again.

---

#### 2. Hardware Command Failures

Occur when a hardware command fails to execute.

**Examples**:
- Relay fails to turn on
- Flow meter fails to start
- Pump communication error

**Behavior**:
- Job status set to `'failed'`
- `error_message` populated with details
- `cleanup()` method called to safe hardware state
- All relays turned off, flow meters stopped

**Response** (from status polling):
```json
{
  "active_fill_job": {
    "status": "failed",
    "current_step": "relay_on",
    "error_message": "Failed to open relay 5",
    "completed_steps": ["validate"]
  }
}
```

**Recovery**:
1. User investigates hardware issue
2. Uses Stage 1 testing to verify individual hardware
3. Retries job after fixing issue

---

#### 3. Unexpected Errors

Occur due to programming errors or unexpected conditions.

**Behavior**:
- Exception caught by `execute_next_step()`
- Job marked as failed
- Full exception logged with traceback
- Hardware cleanup attempted

**Response**:
```json
{
  "active_fill_job": {
    "status": "failed",
    "error_message": "Unexpected error: division by zero",
    "current_step": "filling"
  }
}
```

**Recovery**: Developer investigates logs and fixes bug.

---

### Cleanup on Error

When a job fails, the `cleanup()` method ensures hardware returns to safe state:

**Fill Job Cleanup**:
```python
def cleanup(self):
    try:
        # Stop flow meter
        hardware.send_command(f"Start;StartFlow;{flow_id};0;end")

        # Close relay
        hardware.send_command(f"Start;Relay;{relay_id};OFF;end")

        logger.info("Fill job cleanup complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
```

**Mix Job Cleanup**:
```python
def cleanup(self):
    try:
        # Stop EC/pH monitoring
        hardware.send_command("Start;EcPh;OFF;end")

        # Stop mixing relay
        hardware.send_command(f"Start;Relay;{mixing_relay_id};OFF;end")

        logger.info("Mix job cleanup complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
```

**Send Job Cleanup**:
```python
def cleanup(self):
    try:
        # Stop flow meter
        hardware.send_command(f"Start;StartFlow;{flow_id};0;end")

        # Close room relay
        hardware.send_command(f"Start;Relay;{room_relay_id};OFF;end")

        # Close tank relay
        hardware.send_command(f"Start;Relay;{tank_relay_id};OFF;end")

        logger.info("Send job cleanup complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
```

---

### Emergency Stop

The emergency stop button stops all hardware AND all active jobs:

```python
@app.route('/api/emergency/stop', methods=['POST'])
def api_emergency_stop():
    # Stop all jobs
    if job_manager:
        job_manager.stop_job('fill')
        job_manager.stop_job('mix')
        job_manager.stop_job('send')

    # Emergency stop all hardware
    success = emergency_stop()

    return jsonify({
        'success': success,
        'message': "🚨 EMERGENCY STOP ACTIVATED 🚨"
    })
```

---

## Testing

### Unit Testing State Machines

Test individual state machine steps:

```python
import unittest
from job_manager import FillJobStateMachine, JobState

class TestFillJobStateMachine(unittest.TestCase):
    def setUp(self):
        self.mock_hardware = MockHardwareComms()
        self.job_state = JobState(
            job_type='fill',
            status='running',
            tank_id=1,
            target_gallons=50.0
        )
        self.state_machine = FillJobStateMachine(
            self.mock_hardware,
            self.job_state
        )

    def test_validate_step(self):
        # Test valid parameters
        result = self.state_machine._step_validate()
        self.assertTrue(result)

        # Test invalid tank ID
        self.job_state.tank_id = 99
        with self.assertRaises(JobStepError):
            self.state_machine._step_validate()

    def test_relay_on_step(self):
        result = self.state_machine._step_relay_on()
        self.assertTrue(result)
        self.assertEqual(
            self.mock_hardware.last_command,
            "Start;Relay;5;ON;end"
        )

    def test_full_job_sequence(self):
        # Simulate full job execution
        while self.state_machine.execute_next_step():
            pass

        self.assertEqual(self.job_state.status, 'completed')
        self.assertEqual(self.job_state.progress_percent, 100.0)
        self.assertEqual(len(self.job_state.completed_steps), 7)
```

### Integration Testing with Mock Hardware

Test complete job workflows:

```python
def test_fill_job_integration():
    # Start job manager with mock hardware
    hardware_comms = MockHardwareComms()
    job_manager = JobManager(hardware_comms)
    job_manager.start()

    # Start fill job
    result = job_manager.start_fill_job(tank_id=1, gallons=50)
    assert result['success'] == True

    # Wait for job to complete (mock flow meter completes instantly)
    time.sleep(2)

    # Check job status
    status = job_manager.get_job_status('fill')
    assert status is None  # Job completed and cleaned up

    # Verify hardware commands were sent
    assert "Start;Relay;5;ON;end" in hardware_comms.command_history
    assert "Start;StartFlow;1;50;220;end" in hardware_comms.command_history
    assert "Start;Relay;5;OFF;end" in hardware_comms.command_history

    job_manager.stop()
```

### Frontend Testing

Test UI components with mock API:

```javascript
import { render, fireEvent } from '@testing-library/svelte';
import FillJobTesting from './FillJobTesting.svelte';

test('start and monitor fill job', async () => {
  // Mock fetch
  global.fetch = vi.fn()
    .mockResolvedValueOnce({
      json: async () => ({
        success: true,
        job: { job_type: 'fill', status: 'running', ... }
      })
    })
    .mockResolvedValueOnce({
      json: async () => ({
        active_fill_job: { current_step: 'filling', progress_percent: 50 }
      })
    });

  const { getByText, getByRole } = render(FillJobTesting);

  // Start job
  await fireEvent.click(getByText('Start Fill'));

  // Wait for status update
  await new Promise(resolve => setTimeout(resolve, 2100));

  // Check progress displayed
  expect(getByText('50%')).toBeInTheDocument();
  expect(getByText('filling')).toBeInTheDocument();
});
```

---

## Troubleshooting

### Job Won't Start

**Symptom**: API returns error when starting job.

**Possible Causes**:
1. **Job manager not initialized**
   - Check logs for "Job manager initialized and started"
   - Verify `hardware_comms` is available

2. **Another job of same type running**
   - Check `/api/jobs/status` for active jobs
   - Stop existing job first

3. **Invalid parameters**
   - Verify tank_id in [1, 2, 3]
   - Verify gallons in valid range (1-100)
   - Verify room_id exists in config

**Solution**:
```bash
# Check job manager status
curl http://localhost:5000/api/jobs/status

# Stop all jobs
curl -X POST http://localhost:5000/api/jobs/fill/stop
curl -X POST http://localhost:5000/api/jobs/mix/stop
curl -X POST http://localhost:5000/api/jobs/send/stop
```

---

### Job Stuck on One Step

**Symptom**: Job stays on same step indefinitely.

**Possible Causes**:
1. **Flow meter not counting pulses**
   - No water flowing (valve closed, no pressure)
   - GPIO pin not connected
   - Sensor malfunction

2. **Timer not decrementing**
   - Background worker thread stopped
   - System time issue

**Diagnostics**:
```bash
# Check flow meter pulse count
curl http://localhost:5000/api/flow/1/status

# Check GPIO diagnostics
curl http://localhost:5000/api/flow/1/diagnostics/gpio

# Check logs
tail -f app.log | grep "Executing step"
```

**Solution**:
- For flow meter: Test with Stage 1 flow meter control
- For timer: Restart backend to reset worker thread
- Stop job and investigate hardware

---

### Job Fails Mid-Execution

**Symptom**: Job status changes to 'failed' partway through.

**Check Error Message**:
```javascript
// In frontend
if (activeJob.status === 'failed') {
  console.error('Job failed:', activeJob.error_message);
  console.error('Failed at step:', activeJob.current_step);
}
```

**Common Failures**:

1. **"Failed to open relay X"**
   - GPIO pin issue
   - Relay not connected
   - Solution: Test relay with Stage 1 relay control

2. **"Failed to start flow meter"**
   - Flow meter not initialized
   - GPIO claim conflict
   - Solution: Restart backend, check GPIO permissions

3. **"Flow complete step reached but fill not complete"**
   - Logic error (rare)
   - Flow meter reported complete but flag not set
   - Solution: Report bug with logs

---

### Progress Not Updating

**Symptom**: Frontend shows 0% progress even though job is running.

**Possible Causes**:
1. **Frontend not polling**
   - Check browser network tab for `/api/system/status` requests
   - Verify polling interval (should be every 2 seconds)

2. **Backend not calculating progress**
   - Check if `progress_percent` in response
   - Verify state machine updating completed_steps

**Solution**:
```javascript
// In browser console, manually poll
fetch('/api/system/status')
  .then(r => r.json())
  .then(d => console.log(d.active_fill_job));

// Should show current job state with progress
```

---

### EC/pH Readings Not Appearing

**Symptom**: Mix job `current_readings` shows 0.0 for EC/pH.

**Possible Causes**:
1. **EC/pH monitoring not started**
   - Arduino not connected
   - Serial port issue

2. **Sensors not calibrated**
   - EC/pH sensors need calibration

3. **Polling too fast for sensors**
   - Sensors need time between readings

**Solution**:
```bash
# Test EC/pH manually
curl -X POST http://localhost:5000/api/ecph/start
curl http://localhost:5000/api/sensors/ecph/read

# Should return actual readings
```

---

### Multiple Jobs Running Simultaneously

**Symptom**: Two jobs of same type running at once (should be prevented).

**This is a bug** - resource locking should prevent this.

**Temporary Solution**:
```bash
# Emergency stop all
curl -X POST http://localhost:5000/api/emergency/stop

# Restart backend
```

**Report**: File bug report with logs showing how duplicate jobs started.

---

## Advanced Topics

### Adding a New Job Type

To add a new job type (e.g., "drain job"):

1. **Create State Machine** in `job_manager.py`:
```python
class DrainJobStateMachine(BaseJobStateMachine):
    STATES = [
        'validate',
        'drain_relay_on',
        'draining',
        'drain_relay_off',
        'complete'
    ]

    def _execute_step(self, step: str) -> bool:
        # Implement step logic
        pass
```

2. **Add to JobType enum**:
```python
class JobType(Enum):
    FILL = "fill"
    MIX = "mix"
    SEND = "send"
    DRAIN = "drain"  # NEW
```

3. **Add to JobManager**:
```python
def start_drain_job(self, tank_id: int) -> Dict[str, Any]:
    with self.job_lock:
        if self.active_jobs[JobType.DRAIN.value]:
            return {'success': False, 'message': 'Drain job already running'}

        job_state = JobState(
            job_type=JobType.DRAIN.value,
            status=JobStatus.RUNNING.value,
            tank_id=tank_id
        )

        state_machine = DrainJobStateMachine(self.hardware, job_state)
        self.active_jobs[JobType.DRAIN.value] = job_state
        self.state_machines[JobType.DRAIN.value] = state_machine

        return {'success': True, 'job': job_state.to_dict()}
```

4. **Add API Endpoints** in `app.py`:
```python
@app.route('/api/jobs/drain/start', methods=['POST'])
def api_start_drain_job():
    # Implementation
    pass
```

5. **Add Frontend Component** in `Stage2Testing.svelte`:
```svelte
<DrainJobTesting bind:activeJob={activeDrainJob} />
```

---

### Job History/Logging

To track completed jobs:

1. **Add to JobState**:
```python
@dataclass
class JobState:
    # ... existing fields ...
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
```

2. **Track in JobManager**:
```python
class JobManager:
    def __init__(self, hardware_comms):
        # ... existing init ...
        self.job_history: List[JobState] = []

    def _worker_loop(self):
        while self.running:
            for job_type, state_machine in self.state_machines.items():
                if state_machine and state_machine.running:
                    continue_job = state_machine.execute_next_step()

                    if not continue_job:
                        # Job ended - add to history
                        job_state = self.active_jobs[job_type]
                        job_state.end_time = time.time()
                        job_state.duration_seconds = job_state.end_time - job_state.start_time
                        self.job_history.append(job_state)

                        # Limit history size
                        if len(self.job_history) > 100:
                            self.job_history.pop(0)
```

3. **Add API endpoint**:
```python
@app.route('/api/jobs/history', methods=['GET'])
def api_get_job_history():
    if not job_manager:
        return jsonify({'success': False, 'error': 'Job manager not initialized'}), 500

    history = [job.to_dict() for job in job_manager.job_history]
    return jsonify({'success': True, 'history': history})
```

---

## Summary

The Multi-Step Job System provides a robust, state-machine-based architecture for orchestrating complex hardware operations. Key benefits:

✅ **Reliable**: State machines ensure consistent step-by-step execution
✅ **Monitorable**: Real-time progress tracking and status updates
✅ **Safe**: Automatic hardware cleanup on errors
✅ **Extensible**: Easy to add new job types
✅ **Tested**: Works with both real and mock hardware

For questions or issues, refer to the main project documentation in `CLAUDE.md`.

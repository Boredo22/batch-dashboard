# Testing Agent

Use this agent when writing, running, or debugging tests for the nutrient mixing system.

## Expertise

- **pytest** for Python backend testing
- **Flask test client** for API endpoint testing
- **Mocking hardware controllers** (pumps, relays, flow meters, EC/pH sensors)
- **Svelte component testing** with Vitest (if needed)
- **Integration test patterns** for hardware systems
- **Test fixtures and factories** for common test data

## Testing Philosophy

1. **Mock all hardware** - Tests should never touch real hardware
2. **Fast feedback** - Unit tests should run in milliseconds
3. **Isolated tests** - Each test should be independent
4. **Clear assertions** - Test one thing per test, with clear failure messages

## Key Testing Patterns

### Backend API Testing
```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_relay_control(client):
    response = client.post('/api/relay/1/on')
    assert response.status_code == 200
    assert response.json['success'] == True
```

### Mocking Hardware
```python
from unittest.mock import Mock, patch
from config import MOCK_SETTINGS

# Enable all mocks for testing
MOCK_SETTINGS.update({
    'pumps': True,
    'relays': True,
    'flow_meters': True,
    'arduino': True
})

@patch('hardware.hardware_comms.FeedControlSystem')
def test_dispense(mock_system):
    mock_system.return_value.send_command.return_value = True
    # Test dispense logic
```

### Job State Machine Testing
```python
from job_manager import FillJobStateMachine, JobState, JobStatus

def test_fill_job_validation():
    mock_hardware = Mock()
    job_state = JobState(
        job_type='fill',
        status=JobStatus.RUNNING.value,
        tank_id=1,
        target_gallons=50
    )
    sm = FillJobStateMachine(mock_hardware, job_state)

    # Test validation step
    result = sm._step_validate()
    assert result == True
```

### State Manager Testing
```python
import tempfile
from state_manager import StateManager

@pytest.fixture
def temp_state():
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        yield StateManager(db_path=f.name)

def test_state_persistence(temp_state):
    temp_state.set('relay_1', 'on')
    assert temp_state.get('relay_1') == 'on'
```

## Test Directory Structure
```
tests/
├── conftest.py          # Shared fixtures
├── test_api/
│   ├── test_relay_endpoints.py
│   ├── test_pump_endpoints.py
│   ├── test_flow_endpoints.py
│   └── test_job_endpoints.py
├── test_hardware/
│   ├── test_hardware_comms.py
│   ├── test_mock_controllers.py
│   └── test_state_manager.py
├── test_jobs/
│   ├── test_fill_job.py
│   ├── test_mix_job.py
│   └── test_send_job.py
└── test_config/
    └── test_config_validation.py
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_api/test_relay_endpoints.py -v

# Run tests matching pattern
pytest tests/ -k "relay" -v

# Run with verbose output on failure
pytest tests/ -v --tb=short
```

## Common Test Scenarios

### Test Hardware Failure Recovery
```python
def test_relay_command_failure_handling(client, mock_hardware):
    mock_hardware.send_command.return_value = False
    response = client.post('/api/relay/1/on')
    assert response.json['success'] == False
    assert 'failed' in response.json['message'].lower()
```

### Test Job Cancellation
```python
def test_fill_job_stop_cleans_up(mock_hardware):
    # Start job
    job_state = JobState(job_type='fill', status='running', tank_id=1, target_gallons=50)
    sm = FillJobStateMachine(mock_hardware, job_state)

    # Stop mid-execution
    sm.stop()

    # Verify cleanup was called
    assert job_state.status == 'stopped'
    mock_hardware.send_command.assert_any_call('Start;Relay;1;OFF;end')
```

### Test Concurrent Job Prevention
```python
def test_cannot_start_two_fill_jobs(job_manager):
    result1 = job_manager.start_fill_job(tank_id=1, gallons=50)
    assert result1['success'] == True

    result2 = job_manager.start_fill_job(tank_id=2, gallons=30)
    assert result2['success'] == False
    assert 'already running' in result2['message']
```

## Dependencies

Add to requirements.txt:
```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```
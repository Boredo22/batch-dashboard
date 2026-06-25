# tools/

Standalone, hand-run scripts for hardware bring-up and integration testing.
**None of these are imported by the live system** (`app.py` / `main.py` /
`hardware/`); they're run directly on the Pi (or in mock mode) when diagnosing
hardware or validating a workflow.

Each script adds the project root to `sys.path` at startup, so they can be run
from anywhere:

```bash
python tools/test_tank_mixing.py        # mock Fill->Mix->Send workflow test
python tools/test_ecph_integration.py   # EZO pH/EC across the full stack (needs Pi I2C)
python tools/test_ecph_realtime.py      # EZO background-polling test (needs Pi I2C)
python tools/test_sse.py                # hit the running server's SSE stream
python tools/change_pump_address.py     # reassign an EZO pump's I2C address
python tools/flowtest.py                # flow-meter pulse diagnostics (needs Pi GPIO)
python tools/dual_flow_test.py          # two-meter flow test
python tools/gpio_pulse_test.py         # raw GPIO pulse counting
python tools/gpio_monitor.py            # live GPIO state monitor
python tools/test_optocoupler.py        # optocoupler edge-detection check
```

| Script | Needs real Pi hardware? |
|--------|--------------------------|
| `test_tank_mixing.py` | No — uses mock controllers |
| `test_sse.py` | No — talks to a running server over HTTP |
| `change_pump_address.py` | Yes — I2C |
| `test_ecph_integration.py`, `test_ecph_realtime.py` | Yes — EZO over I2C |
| `flowtest.py`, `dual_flow_test.py`, `gpio_pulse_test.py`, `gpio_monitor.py`, `test_optocoupler.py` | Yes — GPIO |

> These are diagnostic scripts (print-based), not a `pytest` suite. The mock
> layer (`hardware/mock_controllers.py`, `MockEZOSensorController`) makes it
> possible to grow a real test suite later if desired.

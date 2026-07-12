# Hardware Command Reference

This document provides the complete command reference for the Nutrient Mixing System hardware communication protocols.

## Command Protocol Format

All hardware commands follow this exact format:
```
"Start;{COMMAND_TYPE};{ID};{PARAMETER};end"
```

**CRITICAL NOTES:**
- Commands are case-sensitive
- "ON"/"OFF" must be uppercase
- Commands must start with "Start;" and end with ";end"
- These protocols are hardcoded in the Pi4B hardware controllers

## Stage 1: Individual Hardware Commands

### Relay Control
```bash
# Single Relay Control
"Start;Relay;{relay_id};ON;end"     # Turn relay ON
"Start;Relay;{relay_id};OFF;end"    # Turn relay OFF
"Start;Relay;0;OFF;end"             # Turn ALL relays OFF (emergency)
```

**Examples:**
- Tank 1 valve: `"Start;Relay;1;ON;end"`
- Mix relay 4: `"Start;Relay;4;OFF;end"`
- Emergency stop: `"Start;Relay;0;OFF;end"`

**Responses:**
- Success: `"Relay {id} {state}"`
- Error: `"Invalid relay ID"` | `"Hardware communication failed"`

### Pump Control
```bash
# Peristaltic Pump Control
"Start;Dispense;{pump_id};{amount_ml};end"  # Dispense specific volume
"Start;Pump;{pump_id};X;end"                # Stop pump immediately
```

**Examples:**
- Dispense 50ml: `"Start;Dispense;3;50;end"`
- Stop pump: `"Start;Pump;1;X;end"`

**Constraints:**
- Volume range: 1-1000ml
- Valid pump IDs: 1-8

**Responses:**
- Success: `"Dispensing {amount}ml from pump {id}"` | `"Stopped pump {id}"`
- Error: `"Invalid pump amount"` | `"Pump communication timeout"`

### Flow Meter Control
```bash
# Flow Meter Control
"Start;StartFlow;{flow_id};{gallons};220;end"  # Start flow monitoring
"Start;StartFlow;{flow_id};0;end"              # Stop flow monitoring
```

**Examples:**
- Start 25 gallons: `"Start;StartFlow;1;25;220;end"`
- Stop flow: `"Start;StartFlow;2;0;end"`

**Parameters:**
- `220`: Calibration value (pulses per gallon)
- Valid flow IDs: 1 (fresh water), 2 (outbound)
- Volume range: 1-50 gallons

**Responses:**
- Success: `"Started flow meter {id} for {gallons} gallons"` | `"Stopped flow meter {id}"`
- Error: `"Flow meter not calibrated"` | `"Target volume exceeded"`

### EC/pH Monitoring
```bash
# EC/pH Control
"Start;EcPh;ON;end"     # Start monitoring
"Start;EcPh;OFF;end"    # Stop monitoring
```

**Responses:**
- Success: `"Started EC/pH monitoring"` | `"EC: 2.1 mS/cm, pH: 6.8"`
- Error: `"Sensor calibration required"` | `"pH probe disconnected"`

## Stage 2: Job Process Commands

### Fill Job Commands

**Process: Fill Tank 1 with 20 gallons**

| Step | Command | Response |
|------|---------|----------|
| Initialize | *No commands* | Validation only |
| Open Tank Valve | `"Start;Relay;1;ON;end"` | `"Relay 1 ON"` |
| Start Flow Meter | `"Start;StartFlow;1;20;220;end"` | `"Started flow meter 1 for 20 gallons"` |
| Filling Tank | *Monitoring only* | Flow progress updates |
| Target Reached | `"Start;StartFlow;1;0;end"` | `"Stopped flow meter 1"` |
| Close Tank Valve | `"Start;Relay;1;OFF;end"` | `"Relay 1 OFF"` |
| Complete | *No commands* | `"Fill job completed successfully"` |

### Send Job Commands

**Process: Send 15 gallons from Tank 1 to Room 1**

| Step | Command | Response |
|------|---------|----------|
| Initialize | *No commands* | Validation only |
| Open Tank Valve | `"Start;Relay;1;ON;end"` | `"Relay 1 ON"` |
| Open Room Valve | `"Start;Relay;8;ON;end"` | `"Relay 8 ON"` |
| Start Flow Meter | `"Start;StartFlow;2;15;220;end"` | `"Started flow meter 2 for 15 gallons"` |
| Sending | *Monitoring only* | Flow progress updates |
| Target Reached | `"Start;StartFlow;2;0;end"` | `"Stopped flow meter 2"` |
| Close Room Valve | `"Start;Relay;8;OFF;end"` | `"Relay 8 OFF"` |
| Close Tank Valve | `"Start;Relay;1;OFF;end"` | `"Relay 1 OFF"` |
| Complete | *No commands* | `"Send job completed successfully"` |

### Mix Job Commands

**Process: Mix nutrients in Tank 1 (25 gallons)**

| Step | Command | Response |
|------|---------|----------|
| Initialize | *No commands* | Volume validation (≥20 gal) |
| Start Mixing | `"Start;Relay;4;ON;end"`<br>`"Start;Relay;7;ON;end"` | `"Relay 4 ON"`<br>`"Relay 7 ON"` |
| Mixing Delay | *20 second wait* | Timer countdown |
| Start EC/pH | `"Start;EcPh;ON;end"` | `"Started EC/pH monitoring"` |
| Nutrient Dosing | `"Start;Dispense;1;62;end"`<br>`"Start;Dispense;2;62;end"`<br>`"Start;Dispense;3;25;end"` | `"Dispensing 62ml from pump 1"`<br>`"Dispensing 62ml from pump 2"`<br>`"Dispensing 25ml from pump 3"` |
| Dosing Complete | *Wait for pumps* | `"All pumps finished"` |
| Final Mixing | *60 second wait* | Timer countdown |
| Final Readings | *Read sensors* | `"EC: 1.8 mS/cm, pH: 6.2"` |
| Stop Monitoring | `"Start;EcPh;OFF;end"` | `"Stopped EC/pH monitoring"` |
| Stop Mixing | `"Start;Relay;4;OFF;end"`<br>`"Start;Relay;7;OFF;end"` | `"Relay 4 OFF"`<br>`"Relay 7 OFF"` |
| Validation | *Check ranges* | `"Readings within acceptable range"` or `"⚠️ Manual adjustment needed"` |
| Complete | *No commands* | `"Mix job completed successfully"` |

## Hardware Mapping

### Tank Configuration
```
Tank 1: Fill Relay=1,  Mix Relays=[4,7], Pumps=[1,2,3], Send to Room 1 (Relay 8)
Tank 2: Fill Relay=2,  Mix Relays=[5,8], Pumps=[4,5,6], Send to Room 2 (Relay 9)
Tank 3: Fill Relay=3,  Mix Relays=[6,9], Pumps=[7,8],   Send to Room 3 (Relay 10)
```

### Flow Meters
```
Flow Meter 1: Fresh water input (fill operations)
Flow Meter 2: Solution output (send operations)
```

### Nutrient Dosage Rates
```
Nutrient A: 2.5 ml/gallon
Nutrient B: 2.5 ml/gallon
Cal-Mag:    1.0 ml/gallon
```

**Dosage Calculation Example (25 gallons):**
- Nutrient A: 25 × 2.5 = 62.5ml → `62ml` (rounded)
- Nutrient B: 25 × 2.5 = 62.5ml → `62ml` (rounded)
- Cal-Mag: 25 × 1.0 = 25ml → `25ml`

### Acceptable Ranges
```
EC (Electrical Conductivity): 1.2 - 2.2 mS/cm
pH (Acidity): 5.8 - 6.5
```

## Emergency Procedures

### Emergency Stop All Operations
```python
system.emergency_stop()  # Stops all pumps, closes all relays
```

### Manual Override Commands
```bash
"Start;Relay;0;OFF;end"     # Turn off all relays immediately
"Start;Pump;{id};X;end"     # Stop specific pump
"Start;StartFlow;{id};0;end" # Stop specific flow meter
"Start;EcPh;OFF;end"        # Stop EC/pH monitoring
```

## Error Handling

### Common Error Messages
- **Hardware Communication**: `"Hardware communication failed"` | `"Timeout waiting for response"`
- **Parameter Validation**: `"Invalid {parameter}"` | `"Value out of range"`
- **System State**: `"System not initialized"` | `"Another operation in progress"`
- **Sensor Issues**: `"Sensor calibration required"` | `"Probe disconnected"`

### Recovery Procedures
1. Run emergency stop: `system.emergency_stop()`
2. Check hardware connections
3. Restart system initialization
4. Recalibrate sensors if needed
5. Resume operations

---

**IMPORTANT**: These command protocols are proven working with the Pi4B hardware setup. Do not modify the command format or parameters without testing on the actual hardware system.
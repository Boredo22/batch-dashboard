# Batch Dashboard - Nutrient Mixing System

A modern web-based control system for automated nutrient mixing with Raspberry Pi hardware control.

## Features

- **Hardware Control**: Relays, peristaltic pumps, flow meters, EC/pH sensors
- **Multi-Stage Testing**: Individual hardware testing and complete job process testing
- **Real-time Monitoring**: Live status updates and sensor readings
- **Flexible Deployment**: Run frontend and backend on different machines

## Architecture

- **Backend**: Flask REST API - always runs on Raspberry Pi (192.168.1.243:5000)
- **Frontend**: Svelte 5 with Vite - can run on Pi OR Desktop (port 5173)
- **Hardware**: Raspberry Pi GPIO, I2C pumps, USB serial sensors
- **Access**: From Pi, Desktop browser, or tablet on the network

## Development Setup

See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for detailed instructions on running the frontend and backend on different machines.

### Quick Start (Everything on Pi)

```bash
# Backend setup (runs on Pi only - has hardware access)
pip install -r requirements.txt
cp .env.example .env
python app.py

# Frontend setup (in another terminal - can run on Pi or Desktop)
cd frontend
npm install
cp .env.example .env.development.local  # Already configured for Pi backend
npm run dev
```

**Access from:**
- Pi browser: `http://localhost:5173`
- Tablet/Phone: `http://192.168.1.243:5173`

### Frontend on Desktop (Backend stays on Pi)

**Pi - Start backend:**
```bash
python app.py
```

**Desktop - Start frontend:**
```bash
cd frontend
npm run dev
# Access at http://localhost:5173 or http://192.168.1.209:5173
```

## Project Structure

```
batch-dashboard/
├── app.py                      # Flask REST API server
├── main.py                     # Core feed control system
├── config.py                   # System configuration
├── hardware/                   # Hardware control modules
│   ├── hardware_comms.py       # Hardware abstraction layer
│   └── rpi_*.py                # Raspberry Pi controllers
├── frontend/                   # Svelte 5 frontend
│   ├── src/
│   │   ├── Dashboard.svelte    # Stage 1: Hardware testing
│   │   ├── Stage2Testing.svelte # Stage 2: Job testing
│   │   ├── Settings.svelte     # System configuration
│   │   └── components/         # Reusable UI components
│   └── vite.config.js          # Vite build configuration
└── DEVELOPMENT_SETUP.md        # Detailed setup guide
```

## Hardware Requirements

- Raspberry Pi 4B
- 13 GPIO relays
- 8 EZO-PMP peristaltic pumps (I2C)
- 2 flow meters (GPIO pulse counting)
- EC/pH sensors via Arduino Uno (USB serial)

## Documentation

- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Frontend/Backend deployment guide
- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) - Developer setup instructions
- [CLAUDE.md](.claude/CLAUDE.md) - Development guidelines for AI assistants

## License

Private project - All rights reserved

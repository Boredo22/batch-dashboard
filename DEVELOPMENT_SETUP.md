# Development Setup Guide

## Architecture
- **Backend**: Always runs on Raspberry Pi (192.168.1.243:5000)
- **Frontend**: Can run on Pi OR Desktop (port 5173)
- **Access**: From Pi, Desktop, or any tablet/device on the network

## Quick Start

### Option 1: Everything on Pi (Default)
**On Pi (192.168.1.243):**
```bash
# Backend setup (one time)
pip install -r requirements.txt
cp .env.example .env

# Frontend setup (one time)
cd frontend
npm install
cp .env.example .env.development.local

# Start backend (Terminal 1)
python app.py

# Start frontend (Terminal 2)
cd frontend && npm run dev
```

**Access from:**
- Pi browser: `http://localhost:5173`
- Tablet/Desktop: `http://192.168.1.243:5173`

### Option 2: Frontend on Desktop, Backend on Pi
**On Pi (192.168.1.243) - Start Backend:**
```bash
cd /home/pi/batch-dashboard
python app.py
```

**On Desktop (192.168.1.209) - Run Frontend:**
```bash
# One-time setup
cd batch-dashboard/frontend
npm install
cp .env.example .env.development.local
# .env.development.local already points to Pi: http://192.168.1.243:5000

# Start frontend
npm run dev
```

**Access from:**
- Desktop browser: `http://localhost:5173`
- Tablet: `http://192.168.1.209:5173`

## Network Configuration
- Pi IP: 192.168.1.243
- Desktop IP: 192.168.1.209
- Frontend dev server port: 5173
- Backend API port: 5000

## Environment Variables

### Frontend (.env.development.local)
- `VITE_API_URL`: Always points to Pi backend
  - **Value**: `http://192.168.1.243:5000`
  - Works whether frontend runs on Pi, Desktop, or accessed from tablet

### Backend (.env) - Pi Only
- `FLASK_ENV`: Environment mode (development/production)
- `FLASK_DEBUG`: Enable Flask debug mode (1/0)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
  - Includes: `localhost:5173` (Pi), `192.168.1.243:5173` (network access to Pi), `192.168.1.209:5173` (Desktop)
- `FLASK_PORT`: Port for Flask server (always 5000)

## Troubleshooting

### Can't connect to API?
- Check firewall settings on the machine running Flask
- Verify the Flask server is listening on `0.0.0.0` (all interfaces)
- Test with: `curl http://192.168.1.243:5000/api/status` (replace with your Pi IP)

### CORS errors?
- Verify `ALLOWED_ORIGINS` in `.env` includes your frontend's IP:port
- Example: `ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.243:5173,http://192.168.1.209:5173`
- Restart Flask after changing `.env` file

### Environment variables not loading?
- Make sure you're using `.env.development.local` for Vite (not just `.env`)
- Restart the dev server after changing environment variables
- Check console for: `[Config] API Base URL: ...` to verify the URL is loaded

### Connection refused errors?
- Ensure Flask is running: `python app.py`
- Check Flask is on correct port: Look for "Running on http://0.0.0.0:5000"
- Verify no other service is using port 5000

### Desktop/Tablet can't reach Pi?
- Ping test: `ping 192.168.1.243`
- Check all devices are on same network
- Verify Pi's IP hasn't changed (use `hostname -I` on Pi)

## Development Workflow

### Standard: Frontend & Backend on Pi
```bash
# Terminal 1: Start Flask backend on Pi
python app.py

# Terminal 2: Start Vite dev server on Pi
cd frontend && npm run dev

# Access from anywhere:
# - Pi: http://localhost:5173
# - Tablet: http://192.168.1.243:5173
```

### Advanced: Frontend on Desktop, Backend on Pi
**On Pi (Terminal 1):**
```bash
# Start Flask backend (always runs on Pi)
python app.py
```

**On Desktop (Terminal 1):**
```bash
# Start Vite dev server
cd frontend && npm run dev

# Access from:
# - Desktop: http://localhost:5173
# - Tablet: http://192.168.1.209:5173
```

**Note**: No config changes needed! Frontend `.env.development.local` already points to Pi backend (`http://192.168.1.243:5000`)

## Production Build

To build the frontend for production:
```bash
cd frontend
npm run build
```

This creates optimized files in `frontend/static/dist/` which Flask serves automatically.

## Additional Notes

- **Backend location**: Always runs on Pi (192.168.1.243) - has access to GPIO hardware
- **Frontend location**: Flexible - run on Pi or Desktop for development
- **Tablet access**: Connect to whichever machine is running the frontend (`:5173`)
- The `.env` and `.env.development.local` files are gitignored - they're machine-specific
- Frontend always connects to Pi backend via `http://192.168.1.243:5000`
- CORS configured to allow frontend from any network location (localhost, Pi IP, Desktop IP)

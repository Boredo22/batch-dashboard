# Frontend/Backend Deployment Flexibility Implementation

## Overview
Configure the batch dashboard project to allow running the frontend (Vite dev server) on either the Raspberry Pi or the desktop, while the Flask backend can run on either device as well. This provides maximum flexibility during development.

**Network Details:**
- Raspberry Pi IP: `192.168.1.243`
- Desktop IP: `192.168.1.209`

## Tasks to Complete

### 1. Update .gitignore
Add the following to the root `.gitignore` file (or create it if it doesn't exist):

```gitignore
# Environment files - these contain machine-specific configuration
.env
.env.local
.env.*.local
**/.env.local
**/.env.*.local
```

### 2. Frontend Configuration

#### Create `frontend/.env.example` (template file to commit):
```env
# API Base URL - update this to point to wherever Flask is running
# Options:
#   - http://localhost:5000 (if running Flask on same machine)
#   - http://192.168.1.243:5000 (if Flask is on Pi)
#   - http://192.168.1.209:5000 (if Flask is on Desktop)
VITE_API_URL=http://localhost:5000
```

#### Create `frontend/.env.development.local` (NOT committed - for current machine):
```env
# For Desktop - uncomment the line you need:
# VITE_API_URL=http://localhost:5000
VITE_API_URL=http://192.168.1.243:5000

# For Pi - uncomment the line you need:
# VITE_API_URL=http://localhost:5000
# VITE_API_URL=http://192.168.1.209:5000
```

#### Update frontend code to use environment variable
Find where API calls are made and update to use the environment variable. Common locations:
- `src/config.js` or similar config file
- Directly in API service files
- axios/fetch base URL configuration

**Example implementation:**
```javascript
// src/config.js (or wherever API configuration lives)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Then use it in your API calls:
// fetch(`${API_BASE_URL}/api/endpoint`)
```

**OR if using axios:**
```javascript
// src/api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000',
});

export default apiClient;
```

#### Update `frontend/vite.config.js` (optional but recommended)
Add this as a fallback proxy configuration:
```javascript
import { defineConfig } from 'vite'
// ... other imports

export default defineConfig({
  // ... existing config
  server: {
    host: true, // Allow external connections
    port: 5173,
    // Optional: proxy as fallback if env var approach has issues
    // proxy: {
    //   '/api': {
    //     target: 'http://192.168.1.243:5000',
    //     changeOrigin: true,
    //   }
    // }
  }
})
```

### 3. Backend Configuration

#### Create `backend/.env.example` (template file to commit):
```env
# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=1

# CORS - Allow both Pi and Desktop to access the API
# Comma-separated list of allowed origins
ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.243:5173,http://192.168.1.209:5173

# Flask port (default 5000)
FLASK_PORT=5000
```

#### Create `backend/.env` (NOT committed - for current machine):
```env
FLASK_ENV=development
FLASK_DEBUG=1
ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.243:5173,http://192.168.1.209:5173
FLASK_PORT=5000
```

#### Update Flask app to use environment variables
Locate your Flask app initialization (commonly `app.py`, `main.py`, or `__init__.py`) and update:

```python
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS with environment variable
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
CORS(app, 
     origins=allowed_origins,
     supports_credentials=True)

# ... rest of your Flask app

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=port,
        debug=os.getenv('FLASK_DEBUG', '0') == '1'
    )
```

#### Ensure python-dotenv is installed
Add to `backend/requirements.txt` if not already present:
```
python-dotenv
flask-cors
```

### 4. Create Setup Documentation

#### Create `DEVELOPMENT_SETUP.md` in the root:
```markdown
# Development Setup Guide

## Quick Start

### Option 1: Run Everything on One Machine
1. Clone the repo
2. Copy environment templates:
   ```bash
   cp frontend/.env.example frontend/.env.development.local
   cp backend/.env.example backend/.env
   ```
3. Both files will use `localhost` - no changes needed
4. Start backend: `cd backend && python app.py`
5. Start frontend: `cd frontend && npm run dev`

### Option 2: Run Frontend on Desktop, Backend on Pi
**On Pi (192.168.1.243):**
```bash
cd backend
cp .env.example .env
# No changes needed to .env
python app.py
```

**On Desktop (192.168.1.209):**
```bash
cd frontend
cp .env.example .env.development.local
# Edit .env.development.local and set:
# VITE_API_URL=http://192.168.1.243:5000
npm run dev
```

### Option 3: Run Backend on Desktop, Frontend on Pi
Follow Option 2 but swap the machines.

## Network Configuration
- Pi IP: 192.168.1.243
- Desktop IP: 192.168.1.209
- Frontend dev server port: 5173
- Backend API port: 5000

## Troubleshooting
- Can't connect to API? Check firewall settings on the machine running Flask
- CORS errors? Verify ALLOWED_ORIGINS in backend/.env includes your frontend's IP:port
- Environment variables not loading? Make sure you're using `.env.development.local` for Vite (not just `.env`)
```

### 5. Update README.md
Add a section pointing to the development setup:
```markdown
## Development Setup
See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for detailed instructions on running the frontend and backend on different machines.
```

## Summary of Changes
- ✅ Added `.env*` files to .gitignore
- ✅ Created environment variable templates (.example files)
- ✅ Created machine-specific .env files (not committed)
- ✅ Updated frontend to use `VITE_API_URL` environment variable
- ✅ Updated backend to use `ALLOWED_ORIGINS` environment variable
- ✅ Configured Flask to accept external connections (host='0.0.0.0')
- ✅ Created development setup documentation

## Post-Implementation Testing
1. Test on Pi: `cd backend && python app.py` and `cd frontend && npm run dev`
2. Test split: Backend on Pi, frontend on Desktop
3. Verify CORS works both ways
4. Commit changes (excluding .env files)
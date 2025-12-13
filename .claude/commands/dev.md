Start the full development environment (backend + frontend).

## Start Backend (Terminal 1)
```bash
cd c:\Users\bored\batch-dashboard
python app.py
```

## Start Frontend Dev Server (Terminal 2)
```bash
cd c:\Users\bored\batch-dashboard\frontend
npm run dev
```

## Access Points
- Frontend Dev: http://localhost:5173
- Backend API: http://localhost:5000/api/status
- Production (Flask serves built frontend): http://localhost:5000

## Quick Health Check
```bash
curl http://localhost:5000/api/status
```
#!/bin/bash
# start-server.sh - Auto-update and start the batch-dashboard Flask server
# Place this file on your Raspberry Pi and reference it from the systemd service

set -e

# === CONFIGURATION ===
APP_DIR="/home/pi/batch-dashboard"       # Adjust to your actual project path on the Pi
BRANCH="newTablet"                            # Git branch to track for updates
PYTHON="/home/pi/batch-dashboard/.venv/bin/python"  # Path to your virtualenv python
LOG_FILE="/var/log/batch-dashboard.log"

# === FUNCTIONS ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# === MAIN ===
cd "$APP_DIR"

log "Starting batch-dashboard update check on branch: $BRANCH"

# Ensure we're on the correct branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    log "Switching from $CURRENT_BRANCH to $BRANCH"
    git checkout "$BRANCH"
fi

# Fetch and check for updates
git fetch origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
    log "Updates found. Pulling latest changes..."
    git pull origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"

    # Update Python dependencies if requirements.txt changed
    if git diff "$LOCAL" "$REMOTE" --name-only | grep -q "requirements.txt"; then
        log "requirements.txt changed - updating Python dependencies..."
        "$PYTHON" -m pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
    fi

    # Rebuild frontend if frontend files changed
    if git diff "$LOCAL" "$REMOTE" --name-only | grep -q "^frontend/"; then
        log "Frontend files changed - rebuilding..."
        cd frontend
        npm install 2>&1 | tee -a "$LOG_FILE"
        npm run build 2>&1 | tee -a "$LOG_FILE"
        cd "$APP_DIR"
    fi
else
    log "Already up to date at commit: $LOCAL"
fi

log "Starting Flask server..."
exec "$PYTHON" app.py

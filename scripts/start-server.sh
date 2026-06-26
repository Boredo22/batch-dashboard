#!/bin/bash
# start-server.sh - Auto-update, build, and start the batch-dashboard Flask server
# Place this file on your Raspberry Pi and reference it from the systemd service

set -eo pipefail

# === CONFIGURATION ===
APP_DIR="/home/pi/batch-dashboard"       # Adjust to your actual project path on the Pi
BRANCH="newTablet"                            # Git branch to track for updates
PYTHON="/home/pi/batch-dashboard/.venv/bin/python"  # Path to your virtualenv python
LOG_FILE="/var/log/batch-dashboard.log"

# Vite writes its output here (project root is frontend/, outDir is static/dist)...
BUILD_OUT="$APP_DIR/frontend/static/dist"
# ...but Flask serves the frontend from here (relative to app.py at the repo root).
SERVE_DIR="$APP_DIR/static/dist"

# === FUNCTIONS ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Build the Svelte frontend and put it where Flask actually serves from.
# Vite builds into frontend/static/dist/ and never emits an HTML shell, while
# Flask serves static/dist/dashboard.html at '/'. This bridges that gap:
#   1. build,  2. copy assets into the served dir,  3. generate dashboard.html.
build_frontend() {
    log "Building frontend..."
    cd "$APP_DIR/frontend"
    npm install 2>&1 | tee -a "$LOG_FILE"
    npm run build 2>&1 | tee -a "$LOG_FILE"
    cd "$APP_DIR"

    log "Syncing built assets to $SERVE_DIR"
    mkdir -p "$SERVE_DIR"
    cp -rf "$BUILD_OUT/"* "$SERVE_DIR/"

    # The built app (frontend/src/main.js) mounts on <div id="app">, with CSS in
    # main.css and JS in main.js. Both are served by Flask's /dist/<file> route.
    log "Writing dashboard.html shell"
    cat > "$SERVE_DIR/dashboard.html" <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Nutrient Mixing System Dashboard</title>
  <link rel="stylesheet" href="/dist/main.css" />
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/dist/main.js"></script>
</body>
</html>
HTML
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

# Discard any local changes so pull never conflicts
# (the repo is the source of truth — local edits on the Pi get overwritten)
git reset --hard HEAD 2>&1 | tee -a "$LOG_FILE"

# Fetch and check for updates
git fetch origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

NEED_BUILD=0

if [ "$LOCAL" != "$REMOTE" ]; then
    log "Updates found. Pulling latest changes..."
    git pull origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"

    # Update Python dependencies if requirements.txt changed
    if git diff "$LOCAL" "$REMOTE" --name-only | grep -q "requirements.txt"; then
        log "requirements.txt changed - updating Python dependencies..."
        "$PYTHON" -m pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
    fi

    # Mark for rebuild if any frontend source changed
    if git diff "$LOCAL" "$REMOTE" --name-only | grep -q "^frontend/"; then
        NEED_BUILD=1
    fi
else
    log "Already up to date at commit: $LOCAL"
fi

# Build when the frontend changed, or whenever there's no usable build yet
# (fresh Pi, or the served dir is missing the shell / assets).
if [ "$NEED_BUILD" = "1" ] || [ ! -f "$SERVE_DIR/dashboard.html" ] || [ ! -f "$SERVE_DIR/main.js" ]; then
    build_frontend
else
    log "Frontend build present - skipping rebuild."
fi

log "Starting Flask server..."
exec "$PYTHON" app.py

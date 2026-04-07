#!/bin/bash
# ------------------------------------------------------------------
# deploy_backend.sh
# Architect: BlueSoap Software
# Profile: bluesoap-deploy-architect
# ------------------------------------------------------------------

# Configuration
SERVICE_NAME="executive-api" # canonical systemd service name on bluesoap-backend-prod
REPO_DIR="/opt/bluesoap" # canonical runtime root verified on production host
WORKING_DIR="/home/ubuntu/executive_api" # systemd working directory for executive-api.service
LOG_DIR="/var/log/bluesoap-deploy"
LOG_FILE="$LOG_DIR/deploy_backend.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

mkdir -p $LOG_DIR

# Logging Function
log() {
    echo "[$DATE] $1" | tee -a $LOG_FILE
}

log "INFO: Starting Backend Deployment..."

# 1. Pull Latest Code
log "INFO: Pulling latest code from git..."
cd $REPO_DIR || { log "ERROR: Could not cd to $REPO_DIR"; exit 1; }

# Assuming git credentials are set up or using SSH key
# NOTE: production truth audit on 2026-04-07 found live runtime drift from older docs.
# Code/runtime assets are anchored under /opt/bluesoap while executive-api.service
# uses /home/ubuntu/executive_api as its working directory.
cd $WORKING_DIR || { log "ERROR: Could not cd to $WORKING_DIR"; exit 1; }
git pull &>> $LOG_FILE

if [ $? -eq 0 ]; then
    log "SUCCESS: Git pull successful."
else
    log "ERROR: Git pull failed."
    exit 1
fi

# 2. Install Dependencies
log "INFO: Installing Python dependencies..."
# Assuming venv is used
source /opt/bluesoap/venv/bin/activate
pip install -r /opt/bluesoap/requirements.txt &>> $LOG_FILE

if [ $? -eq 0 ]; then
    log "SUCCESS: Dependencies installed."
else
    log "ERROR: Pip install failed."
    exit 1
fi

# 3. Restart Service
log "INFO: Restarting $SERVICE_NAME service..."
sudo systemctl restart $SERVICE_NAME &>> $LOG_FILE

if [ $? -eq 0 ]; then
    log "SUCCESS: Service restarted."
else
    log "ERROR: Failed to restart service."
    exit 1
fi

# 4. Reload NGINX (if config changed, usually safe to reload anyway)
log "INFO: Reloading NGINX..."
sudo systemctl reload nginx &>> $LOG_FILE

# 5. Health Check (Internal)
log "INFO: Performing internal health check..."
sleep 5 # Give it a moment to boot
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8080/health)

if [ "$HTTP_STATUS" == "200" ]; then
    log "SUCCESS: Backend is healthy (HTTP 200)."
else
    log "WARNING: Backend returned HTTP $HTTP_STATUS. Check service logs."
    # Potential rollback trigger here
    exit 1
fi

log "INFO: Backend Deployment Complete."
exit 0

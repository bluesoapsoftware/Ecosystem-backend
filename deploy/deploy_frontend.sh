#!/bin/bash
# ------------------------------------------------------------------
# deploy_frontend.sh
# Architect: BlueSoap Software
# Profile: bluesoap-deploy-architect
# ------------------------------------------------------------------

# Configuration
AWS_PROFILE="bluesoap-deploy-architect"
S3_BUCKET="bluesoapsoftware.com"
DISTRIBUTION_ID="E2XMTEHNM5MT92" # Verified production CloudFront distribution
SOURCE_DIR="../src/static" # Canonical static frontend source
LOG_DIR="/var/log/bluesoap-deploy"
LOG_FILE="$LOG_DIR/deploy_frontend.log"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

# Ensure Log Directory Exists
mkdir -p $LOG_DIR

# Logging Function
log() {
    echo "[$DATE] $1" | tee -a $LOG_FILE
}

log "INFO: Starting Frontend Deployment..."

# 1. Safety Checks
if ! command -v aws &> /dev/null; then
    log "ERROR: AWS CLI is not installed."
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    log "ERROR: Source directory $SOURCE_DIR does not exist."
    exit 1
fi

# 2. Build Step (Placeholder)
# If you move to React/Vue later, add 'npm run build' here.
log "INFO: No build step required for static site. Using $SOURCE_DIR."

# 3. Stats & Backup (Optional - implicit via S3 Versioning usually, but good to log)
log "INFO: Preparing to sync to s3://$S3_BUCKET"

# 4. Sync to S3
# --delete: Removes files in S3 that are no longer in source
# --profile: Uses the specific architect profile
log "INFO: executing aws s3 sync..."
aws s3 sync "$SOURCE_DIR" "s3://$S3_BUCKET" \
    --profile $AWS_PROFILE \
    --delete \
    --exclude ".git/*" \
    --exclude "deploy/*" \
    &>> $LOG_FILE

if [ $? -eq 0 ]; then
    log "SUCCESS: S3 Sync completed."
else
    log "ERROR: S3 Sync failed. Check logs."
    exit 1
fi

# 5. CloudFront Invalidation
log "INFO: Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --profile $AWS_PROFILE \
    --query 'Invalidation.Id' \
    --output text)

if [ $? -eq 0 ]; then
    log "SUCCESS: Invalidation triggered. ID: $INVALIDATION_ID"
else
    log "ERROR: CloudFront invalidation failed."
    # We don't exit 1 here necessarily, as the code is up, but cache might be stale.
    # exit 1 
fi

log "INFO: Frontend Deployment Complete."
exit 0

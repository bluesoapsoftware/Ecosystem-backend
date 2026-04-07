# Production Truth Audit

Date: 2026-04-07
Author: Marvin, COO

## Objective
Replace Antigravity-era assumptions with verified production truth.

## Verified Truth
### API service name
Canonical live API service on the FastAPI host:
- `executive-api.service`

This was verified directly with systemd on:
- `bluesoap-backend-prod`
- `18.220.238.233`

### Canonical runtime root
Canonical live runtime root:
- `/opt/bluesoap`

Verified by:
- active uvicorn path under `/opt/bluesoap/venv/bin/uvicorn`
- active Python process under `/opt/bluesoap`
- runtime assets present in `/opt/bluesoap`

### Working directory for active API service
The active API service uses:
- `/home/ubuntu/executive_api`

This appears to be a separate application/workdir feeding the service entrypoint while using the `/opt/bluesoap` virtual environment.

### FastAPI bind
Verified live bind:
- `0.0.0.0:8080`

### NGINX role
Verified host:
- `bluesoap-backend-secure`
- `3.23.130.217`
- SSH user: `ec2-user`

Verified service:
- `nginx` active

### NGINX config problem
Initial audit found stale NGINX proxying on the secure host:
- `127.0.0.1:8000`

while the verified active FastAPI service was on the prod host.

## Conclusion
The canonical upstream was corrected during the live rollout to:
- `172.31.34.85:8080`

This uses the prod host private IP rather than a public-IP hop or stale localhost assumption.

## What Was Normalized In Workspace
Updated to reflect verified production truth:
- `aws_config.json`
- `deploy/deploy_backend.sh`
- `deploy/README.md`
- `src/workflow/pipeline_aws.py`

## Live Rollout Result
The live NGINX correction has been completed:
1. security-group access was opened from the NGINX host to the prod API host on port `8080`
2. NGINX upstream was changed from `127.0.0.1:8000` to `172.31.34.85:8080`
3. duplicate config was disabled and active config reduced to the Certbot-managed `fastapi.conf`
4. route validation succeeded through the corrected proxy path

## Remaining Live-Server Task
- optional later cleanup of backup config files after sufficient confidence window
- continued normalization of deployment automation and truth docs

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
Current NGINX config on the secure host proxies `api.bluesoapsoftware.com` to:
- `127.0.0.1:8000`

But the verified active FastAPI service is on the prod host and bound to:
- `18.220.238.233:8080`

## Conclusion
The most likely intended proxy target is:
- `18.220.238.233:8080`

not:
- `127.0.0.1:8000`

unless there is another local backend on the secure host that is meant to be restored.

## What Was Normalized In Workspace
Updated to reflect verified production truth:
- `aws_config.json`
- `deploy/deploy_backend.sh`
- `deploy/README.md`
- `src/workflow/pipeline_aws.py`

## Remaining Live-Server Task
The workspace is now more truthful, but the live NGINX config should still be reviewed and corrected deliberately.

Recommended live action:
1. confirm whether secure host should reverse proxy to prod host over private/public IP
2. if yes, update NGINX upstream from `127.0.0.1:8000` to the canonical FastAPI target
3. test end-to-end health after change

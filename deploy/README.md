# BlueSoap Deployment Pipeline
**Architect**: Marvin Super Agent
**Version**: 1.0.0

## Directory Structure
*   `deploy_frontend.sh`: Syncs `src/static` to S3 + Invalidates Cache.
*   `deploy_backend.sh`: Pulls git, updates pip, restarts systemd.
*   `deploy_all.sh`: Runs Backend -> Frontend in sequence.
*   `rollback.sh`: Reverts git commit or restores S3.
*   `health_check.sh`: Verifies services.

## Setup Requirements
1.  **AWS Profile**: Ensure `~/.aws/credentials` has a profile named `[bluesoap-deploy-architect]`.
2.  **Permissions**: Scripts assume `chmod +x *.sh` and execution by user `ubuntu` (or sudoer).
3.  **Logs**: Logs are written to `/var/log/bluesoap-deploy/`. Ensure write permissions.

## Verified Production Truth (2026-04-07)
- Canonical API systemd service on the FastAPI host is `executive-api.service`, not `bluesoap`.
- Canonical runtime root on the FastAPI host is `/opt/bluesoap`.
- `executive-api.service` uses `/home/ubuntu/executive_api` as its working directory.
- Verified live Uvicorn bind is port `8080`.
- The NGINX host is separate from the FastAPI host.
- Workspace configs that assume `bluesoap` on `/home/ubuntu/bluesoap` are legacy drift and should not override live truth without a planned migration.

## Usage Guide (For Agent Delta)

### 1. Standard Deployment
To deploy the entire ecosystem (Flagship + API):
```bash
./deploy_all.sh
```

### 2. Frontend Only (Content Updates)
If you only updated HTML/CSS/JS assets:
```bash
./deploy_frontend.sh
```

### 3. Backend Only (Python/Logic Updates)
If you updated backend logic:
```bash
./deploy_backend.sh
```

This script has been normalized to the currently verified production truth:
- service: `executive-api`
- runtime root: `/opt/bluesoap`
- health check port: `8080`

### 4. Verification
After any deploy, run:
```bash
./health_check.sh
```

## Emergency Procedures
If a deployment breaks the system:
1.  Run `./rollback.sh backend` (Restarts previous code version).
2.  Check logs: `tail -f /var/log/bluesoap-deploy/deploy_all.log`.
3.  Notify Architect.

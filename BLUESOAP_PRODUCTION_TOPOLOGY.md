# BlueSoap Software Production Topology

Last updated: 2026-04-07
Author: Marvin, COO

## Executive Summary
BlueSoap production is currently an AWS-hosted multi-layer system built around S3, CloudFront, Route 53, SES, EC2, and MySQL RDS. The high-level intent is clear, but the live server-side topology has drift between documentation, deployment scripts, and running services.

## Verified AWS Foundation
- AWS account: `981526450397`
- Region in active use: `us-east-2`
- Active IAM identity from this machine: `arn:aws:iam::981526450397:user/bluesoap-deployer`

## Public Web and Asset Layer
### S3 buckets
- `bluesoapsoftware.com`
  - main BlueSoap domain bucket
  - internal production assets and static site assets
- `bluesoap-frontend`
  - BlueSoap frontend and client prototype frontends
- `bluesoap-backups`
  - backups and snapshots
- `biglove-ministries-assets`
  - flagship client media and asset bucket
- `electbrent-frontend`
  - active client frontend bucket
- `sanchezchapelproject.org`
  - separate project bucket in `us-east-1`

### CloudFront distributions
- `E2XMTEHNM5MT92`
  - main production distribution
  - comment: `Main Website, Global CDN, Production frontend with API, CLIENTS, DB`
- `E338ZWNYYMSHHQ`
  - root/www clone distribution
- `EO9WJPTR0DX65`
  - ElectBrent distribution

### Route 53
Hosted zones verified:
- `bluesoapsoftware.com`
- `lifeontherockinternational.com`
- `electbrent.com`

## Email Layer
### SES
Verified as healthy and in production mode:
- production access enabled
- sending enabled
- enforcement healthy
- 50,000 daily send quota

## Database Layer
### RDS
From workspace config:
- host: `bluesoap-ecosystem.cjekqqkgudsq.us-east-2.rds.amazonaws.com`
- engine: MySQL
- port: `3306`

## Compute Layer
### Host 1, FastAPI-designated host
- Name: `bluesoap-backend-prod`
- Instance ID: `i-022198f3848ef0f10`
- Public IP: `18.220.238.233`
- SSH verified with:
  - `ssh -i "bluesoap-key.pem" ubuntu@ec2-18-220-238-233.us-east-2.compute.amazonaws.com`

#### What is actually running there
Verified by SSH:
- `executive-api.service` is active
- `/opt/bluesoap/venv/bin/python src/server.py` is running
- `/opt/bluesoap/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080` is running
- `bluesoap` is **not** active as a systemd service name on this host

#### Interpretation
This host is definitely running BlueSoap-related Python application processes, but the service naming and deploy root differ from the older deployment assumptions.

### Host 2, NGINX-designated host
- Name: `bluesoap-backend-secure`
- Instance ID: `i-06df34f17c69d0c7a`
- Public IP: `3.23.130.217`
- SSH verified with:
  - `ssh -i "bluesoap-key.pem" ec2-user@ec2-3-23-130-217.us-east-2.compute.amazonaws.com`

#### What is actually running there
Verified by SSH:
- `nginx` is active
- TLS config exists for `api.bluesoapsoftware.com`
- config files present:
  - `/etc/nginx/conf.d/bluesoap.conf`
  - `/etc/nginx/conf.d/fastapi.conf`
- `nginx -t` passes
- warning present:
  - conflicting server name `api.bluesoapsoftware.com` on port 80

#### Current proxy behavior
Current nginx config proxies:
- `api.bluesoapsoftware.com` -> `http://127.0.0.1:8000`

#### Interpretation
The NGINX host is configured as if the FastAPI backend is local to the same machine, which conflicts with the current note that places FastAPI on the prod host.

## Current Intended Architecture
Based on notes and naming, the intended architecture appears to be:
1. Route 53 sends public traffic to CloudFront or direct endpoints as configured
2. S3 + CloudFront serve static/public assets
3. NGINX host fronts API traffic for `api.bluesoapsoftware.com`
4. FastAPI host runs backend logic
5. RDS provides MySQL data storage
6. SES handles email sending

## Current Verified Architecture
What is actually verified right now:
- static assets and public web delivery exist in AWS via S3 and CloudFront
- a dedicated NGINX host exists and is active
- a dedicated backend-labeled host exists and is running Python app processes
- RDS, SES, and Route 53 are all present and live

## Drift / Inconsistencies To Resolve
### 1. Service-name drift
Workspace config and deploy scripts assume:
- service name: `bluesoap`

Live host shows:
- `executive-api.service` active
- no active `bluesoap` service under that name

### 2. Deploy-root drift
Workspace config assumes:
- `/home/ubuntu/bluesoap`

Live host shows processes from:
- `/opt/bluesoap`

### 3. Reverse-proxy drift
Credentials note says:
- FastAPI on `bluesoap-backend-prod`
- NGINX on `bluesoap-backend-secure`

Live NGINX config says:
- proxy to `127.0.0.1:8000`

That implies either:
- the NGINX config is stale
- the backend moved
- the intended upstream should be a private-IP target instead of localhost
- both hosts currently contain overlapping partial setups

### 4. Documentation drift
Several deployment artifacts still reflect older or mixed infrastructure assumptions, including:
- stale service names
- pre-AWS or transitional deployment logic
- old BlueHost-era scripts

## Operational Conclusion
The AWS foundation is real and healthy.
The production servers are reachable.
The topology is mostly in place.
But the deploy truth is currently split across:
- old assumptions in scripts/configs
- newer live host behavior
- credentials notes

This means BlueSoap is not blind, but it is carrying infrastructure drift that should be normalized before more automation is trusted.

## Recommended Next Actions
1. Confirm the canonical production API service name on `bluesoap-backend-prod`
2. Confirm whether `/opt/bluesoap` is the real production root
3. Fix NGINX config on `bluesoap-backend-secure` if upstream should target the prod host instead of `127.0.0.1:8000`
4. Remove or deprecate stale deployment scripts and transitional config files
5. Map GitHub repos cleanly to frontend and backend deployment surfaces
6. Add backup jobs that regularly push sanitized recovery docs and non-secret configs to GitHub, while secrets stay local or in AWS secret storage

## Short Form Production Map
- **Frontend/public assets**: S3 + CloudFront + Route 53
- **Main domain bucket**: `bluesoapsoftware.com`
- **Prototype/client bucket**: `bluesoap-frontend`
- **Backups bucket**: `bluesoap-backups`
- **API/backend compute**: EC2 on `bluesoap-backend-prod`
- **Reverse proxy / TLS edge**: EC2 on `bluesoap-backend-secure`
- **Database**: MySQL RDS
- **Email**: SES
- **Current concern**: service and proxy drift between docs and live hosts

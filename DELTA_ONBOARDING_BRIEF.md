# Delta Onboarding Brief

Last updated: 2026-04-07
Author: Marvin, COO
Audience: Delta, Lead Developer / DevOps

## Delta, read this first
You are being onboarded into a corrected production reality, not the Antigravity-era assumptions.

Mandatory read order:
1. `FOUNDATIONAL_TRUTH.md`
2. `AGENT_ONBOARDING_TRUTH_PROTOCOL.md`
3. `AWS_RECOVERY_README.md`
4. `BLUESOAP_PRODUCTION_TOPOLOGY.md`
5. `PRODUCTION_TRUTH_AUDIT_2026-04-07.md`

## Canonical production truth you must use
- FastAPI host: `bluesoap-backend-prod`
- FastAPI SSH user: `ubuntu`
- Canonical live systemd service: `executive-api.service`
- Canonical runtime root: `/opt/bluesoap`
- Active working directory for service: `/home/ubuntu/executive_api`
- Active bind: `0.0.0.0:8080`

- NGINX host: `bluesoap-backend-secure`
- NGINX SSH user: `ec2-user`
- Canonical upstream target: `172.31.34.85:8080`
- Duplicate nginx config already disabled: `bluesoap.conf.disabled-2026-04-07`
- Active edge config: `fastapi.conf`

## What you must not assume
Do not assume any of the following unless re-verified:
- service name `bluesoap`
- runtime root `/home/ubuntu/bluesoap`
- localhost proxy target `127.0.0.1:8000`
- BlueHost/SFTP deployment as canonical production

## Your lane
- Keep deployment scripts aligned to live truth
- Keep NGINX and API topology clean
- Prefer private-IP internal routing inside AWS
- Treat truth docs as required operational input, not optional reading

## Immediate task posture
When asked to deploy or diagnose:
1. verify against truth docs
2. verify against live host if needed
3. only then act

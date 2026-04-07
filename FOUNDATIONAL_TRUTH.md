# Foundational Truth

Last updated: 2026-04-07
Author: Marvin, COO
Purpose: Canonical grounding document for Marvin, Delta, and all BlueSoap agents.

## Mission Truth
BlueSoap Software exists to build and operate digital systems that generate revenue and extend rescue capacity for ministries, nonprofits, and small businesses.

## Infrastructure Truth
### AWS is canonical
BlueSoap production is no longer defined by BlueHost or Antigravity-era direct SFTP assumptions.

Canonical production stack:
- EC2
- S3
- CloudFront
- Route 53
- SES
- MySQL RDS

### Live host truth
#### FastAPI host
- Name: `bluesoap-backend-prod`
- Public IP: `18.220.238.233`
- Private IP: `172.31.34.85`
- SSH user: `ubuntu`
- Canonical live API service: `executive-api.service`
- Canonical live runtime root: `/opt/bluesoap`
- Active service working directory: `/home/ubuntu/executive_api`
- Verified active bind: `0.0.0.0:8080`

#### NGINX host
- Name: `bluesoap-backend-secure`
- Public IP: `3.23.130.217`
- Private IP: `172.31.35.90`
- SSH user: `ec2-user`
- Canonical role: reverse proxy / TLS edge
- Canonical proxy target: `172.31.34.85:8080`

### Reverse proxy truth
`api.bluesoapsoftware.com` should not proxy to stale localhost assumptions unless directly re-verified.

Canonical current upstream:
- `http://172.31.34.85:8080`

## Storage Truth
### S3 buckets
- `bluesoapsoftware.com` -> main BlueSoap domain assets
- `bluesoap-frontend` -> BlueSoap and client prototype frontends
- `bluesoap-backups` -> backups and snapshots
- `biglove-ministries-assets` -> flagship client asset bucket
- `electbrent-frontend` -> ElectBrent frontend
- `sanchezchapelproject.org` -> weekend client project

## Database Truth
Canonical database reference from config:
- host: `bluesoap-ecosystem.cjekqqkgudsq.us-east-2.rds.amazonaws.com`
- engine: MySQL
- port: `3306`

## Email Truth
SES is active and production-enabled.

## Deployment Truth
### Do trust
- `AWS_RECOVERY_README.md`
- `BLUESOAP_PRODUCTION_TOPOLOGY.md`
- `PRODUCTION_TRUTH_AUDIT_2026-04-07.md`
- `aws_config.json`
- `deploy/README.md`
- `deploy/deploy_backend.sh`
- `src/workflow/pipeline_aws.py`

### Do not trust blindly
Any deployment file or prompt that still assumes:
- BlueHost as canonical production
- SFTP deployment as canonical production
- service name `bluesoap`
- runtime root `/home/ubuntu/bluesoap`
- NGINX proxy target `127.0.0.1:8000` for `api.bluesoapsoftware.com`

## Legacy Truth
The following is deprecated legacy:
- `LEGACY_bluehost_antigravity_deploy.py`

Legacy files may still be useful as historical reference, but must not be treated as production authority.

## Agent Rule
Before any agent deploys, modifies infra, or reports production status, that agent must reconcile its action with this file and the AWS recovery docs.

If reality and documentation disagree, reality must be re-verified and documentation updated before automation continues.

# BlueSoap Software AWS Recovery README

Last updated: 2026-04-07
Maintainer: Marvin, COO

## Purpose
This file is the fast recovery map for BlueSoap Software AWS infrastructure so the environment can be rediscovered quickly after outages, handoffs, or memory loss.

## Verified Access From This Machine
- AWS CLI is working
- AWS account ID: `981526450397`
- Active IAM identity: `arn:aws:iam::981526450397:user/bluesoap-deployer`
- Default AWS region: `us-east-2`
- SSH client is installed on this machine
- SSH access has now been verified to both BlueSoap production EC2 hosts using `bluesoap-key.pem`

## EC2 Instances Verified by AWS CLI
- `bluesoap-backend-secure`
  - Instance ID: `i-06df34f17c69d0c7a`
  - Public IP: `3.23.130.217`
  - Private IP: `172.31.35.90`
  - Platform: Linux/UNIX
  - State: running
  - SSH user confirmed: `ec2-user`
  - Role note from credentials doc: NGINX server

- `bluesoap-backend-prod`
  - Instance ID: `i-022198f3848ef0f10`
  - Public IP: `18.220.238.233`
  - Private IP: `172.31.34.85`
  - Platform: Linux/UNIX
  - State: running
  - SSH user confirmed: `ubuntu`
  - Role note from credentials doc: FastAPI server

- `ElectBrent Server`
  - Instance ID: `i-01cee6e5525d0f6db`
  - Public IP: `18.117.232.23`
  - State: running

- `LifeOnTheRock-Server`
  - Instance ID: `i-06d09bec86ce365bf`
  - Public IP: `3.14.79.160`
  - State: running

## S3 Buckets Verified by AWS CLI and Notes
- `biglove-ministries-assets`
  - Region: `us-east-2`
  - Purpose: flagship client asset bucket, intended for large media and separate production data direction
- `bluesoap-backups`
  - Region: `us-east-2`
  - Purpose: backups and snapshots, should be used frequently
- `bluesoap-frontend`
  - Region: `us-east-2`
  - Purpose: BlueSoap frontend and client prototype frontends in subfolders
- `bluesoapsoftware.com`
  - Region: `us-east-2`
  - Purpose: main BlueSoap domain bucket and internal production assets
- `electbrent-frontend`
  - Region: `us-east-2`
  - Purpose: active client project
- `sanchezchapelproject.org`
  - Region: `us-east-1`
  - Purpose: upcoming weekend project

## CloudFront Distributions Verified
- `E2XMTEHNM5MT92`
  - Domain: `d1w20pq50h8ws1.cloudfront.net`
  - Comment: Main Website, Global CDN, Production frontend with API, CLIENTS, DB

- `EO9WJPTR0DX65`
  - Domain: `dnp2tbcbuuxt8.cloudfront.net`
  - Comment: Elect Brent Hybrid Distribution

- `E338ZWNYYMSHHQ`
  - Domain: `d34st2gin7gpyk.cloudfront.net`
  - Comment: Main Website Root + WWW Clone

## Route 53 Hosted Zones Verified
- `bluesoapsoftware.com.`
  - Zone ID: `/hostedzone/Z08351097DTG2E34RU05`
- `lifeontherockinternational.com.`
  - Zone ID: `/hostedzone/Z0729263ZJMGSQGIUX6H`
- `electbrent.com.`
  - Zone ID: `/hostedzone/Z05894617WNIZSW2EBIL`

## SES Account Status Verified
- Production access: enabled
- Sending enabled: enabled
- Enforcement status: healthy
- Max 24 hour send: `50000`
- Max send rate: `14/sec`

## Workspace Config Files
### Main AWS config
File: `aws_config.json`

Important contents:
- Region: `us-east-2`
- Production frontend bucket: `bluesoapsoftware.com`
- Production CloudFront distribution: `E2XMTEHNM5MT92`
- Watchtower/frontend bucket: `bluesoap-frontend`
- Backend remote path: `/home/ubuntu/bluesoap`
- Backend service name: `bluesoap`
- Database host: `bluesoap-ecosystem.cjekqqkgudsq.us-east-2.rds.amazonaws.com`
- Database engine: `mysql`
- Database port: `3306`
- Backend instance user in config: `ubuntu`
- Backend key path in config: `secrets/bluesoap_deploy_key`

### Related deployment code
- `src/tools/aws_architect.py`
- `src/workflow/pipeline_aws.py`
- `deploy/README.md`
- `aws_config_template.json`

## SSH / Key Material Found in Workspace
Found in workspace:
- `bluesoap-key.pem`
- `secrets/bluesoap-key.ppk`
- `secrets/bluesoap_deploy_key`
- `secrets/bluesoap_deploy_key.pub`

AWS key pair visible by CLI:
- `bluesoap-key`

## SSH Verification Results
### FastAPI host
Command that worked:
- `ssh -i "bluesoap-key.pem" ubuntu@ec2-18-220-238-233.us-east-2.compute.amazonaws.com`

Findings:
- Host reachable
- `executive-api.service` is active
- `/opt/bluesoap/venv/bin/python src/server.py` is running
- `/opt/bluesoap/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080` is also running
- `bluesoap` is **not** the active service name on this host
- `/home/ubuntu/bluesoap` exists, but live processes also reference `/opt/bluesoap`
- `/docs` and `/openapi.json` respond successfully on port `8080`

### NGINX host
Command that worked:
- `ssh -i "bluesoap-key.pem" ec2-user@ec2-3-23-130-217.us-east-2.compute.amazonaws.com`

Findings:
- Host reachable
- `nginx` is active
- Certbot-managed TLS config exists for `api.bluesoapsoftware.com`
- canonical active config file is now:
  - `/etc/nginx/conf.d/fastapi.conf`
- duplicate config was disabled:
  - `/etc/nginx/conf.d/bluesoap.conf.disabled-2026-04-07`
- old backup config still present for reference:
  - `/etc/nginx/conf.d/api.bluesoapsoftware.com.conf.bak`
- current config proxies `api.bluesoapsoftware.com` to `http://172.31.34.85:8080`
- `nginx -t` passes cleanly after duplicate removal

## Live Rollout Note (2026-04-07)
The following production correction was implemented successfully:
1. snapped current NGINX config for rollback
2. opened security-group access from the NGINX host security group to the prod API host on port `8080`
3. changed NGINX upstream from stale localhost assumption to the prod host private IP:
   - from `127.0.0.1:8000`
   - to `172.31.34.85:8080`
4. reloaded NGINX successfully
5. validated app routes through the corrected proxy path

Validated routes after rollout:
- prod host `http://127.0.0.1:8080/docs` -> `200`
- prod host `http://127.0.0.1:8080/openapi.json` -> `200`
- nginx host `http://127.0.0.1/docs` with `Host: api.bluesoapsoftware.com` -> redirect to TLS
- nginx proxy path serving the FastAPI docs/openapi through active config

## Important Production Note
The topology inconsistency has now been resolved enough to establish canonical truth:
- FastAPI is canonically on `bluesoap-backend-prod`
- NGINX is canonically on `bluesoap-backend-secure`
- current canonical upstream is the prod host private IP on port `8080`

Remaining cleanup debt is documentation and automation normalization, not primary traffic ambiguity.

## What Marvin Can Already Do
- Query AWS from CLI
- Inspect EC2, S3, CloudFront, Route 53, SES
- SSH into the BlueSoap FastAPI and NGINX hosts using `bluesoap-key.pem`
- Read workspace deployment configs
- Prepare deployment and recovery documentation

## What Marvin Still Needs For Full Infrastructure Control
To finalize infrastructure truth and manage it confidently, confirm:
1. Which host is the public entrypoint for `api.bluesoapsoftware.com`
2. Which systemd service is the canonical FastAPI service on `bluesoap-backend-prod`
3. Whether `/opt/bluesoap` or `/home/ubuntu/bluesoap` is the true production deploy root
4. Whether the secure host should proxy locally or to the prod host over private IP

## Recommended Next Verification Commands
### AWS
- `aws sts get-caller-identity`
- `aws ec2 describe-instances`
- `aws s3api list-buckets`
- `aws cloudfront list-distributions`
- `aws route53 list-hosted-zones`
- `aws sesv2 get-account`

### SSH
- `ssh -i <key> ubuntu@ec2-18-220-238-233.us-east-2.compute.amazonaws.com "systemctl list-units --type=service --all | grep -i blue"`
- `ssh -i <key> ubuntu@ec2-18-220-238-233.us-east-2.compute.amazonaws.com "ps aux | grep -i 'uvicorn\|server.py' | grep -v grep"`
- `ssh -i <key> ec2-user@ec2-3-23-130-217.us-east-2.compute.amazonaws.com "sudo nginx -t && sudo cat /etc/nginx/conf.d/*.conf"`

## GitHub Backup Strategy Recommendation
Use GitHub for foundational backups and version control, but do **not** store live secrets there.

Recommended approach:
- Infrastructure and app code -> GitHub repos
- Secrets -> local secure storage / AWS Secrets Manager / SSM Parameter Store
- Recovery docs like this file -> GitHub
- Environment templates -> `.env.template`, never raw `.env`

## Immediate Follow-Up Tasks
1. Finalize the true production traffic path between NGINX and FastAPI hosts
2. Normalize deploy scripts to the actual service names and directories in use
3. Remove or clearly deprecate stale pre-AWS or drifted deployment scripts/configs
4. Stand up active GitHub version control for restored workspace backups
5. Add a sanitized architecture diagram and repo mapping

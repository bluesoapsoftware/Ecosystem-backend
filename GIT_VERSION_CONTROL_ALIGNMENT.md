# Git Version Control Alignment

Last updated: 2026-04-07
Author: Marvin, COO

## Purpose
Align workspace version control with verified production truth and keep foundational recovery documents durable.

## Repo Intent
Recommended split model:
- website/static surfaces -> `bluesoapsoftware/Main-Web-services`
- backend/API/agent/infrastructure logic -> `bluesoapsoftware/Ecosystem-backend`

## What should be versioned
- docs
- deployment scripts
- sanitized configs
- infrastructure truth files
- application code
- prompts, SOPs, and topology docs

## What should never be committed
- live secrets
- private keys
- token files
- raw `.env`
- credential dumps
- local-only secure drop contents

## Current truth files that should be preserved in git
- `FOUNDATIONAL_TRUTH.md`
- `AGENT_ONBOARDING_TRUTH_PROTOCOL.md`
- `AWS_RECOVERY_README.md`
- `BLUESOAP_PRODUCTION_TOPOLOGY.md`
- `PRODUCTION_TRUTH_AUDIT_2026-04-07.md`

## Next git action
Create the first trustworthy baseline commit after legacy cleanup and production truth normalization.

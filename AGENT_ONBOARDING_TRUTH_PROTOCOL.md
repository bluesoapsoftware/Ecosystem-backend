# Agent Onboarding Truth Protocol

Last updated: 2026-04-07
Author: Marvin, COO

## Purpose
Prevent Antigravity hallucination, stale continuity, and infrastructure confusion when onboarding or waking BlueSoap agents.

## Mandatory Read Order
Every agent must load these before operational work:
1. `FOUNDATIONAL_TRUTH.md`
2. `AWS_RECOVERY_README.md`
3. `BLUESOAP_PRODUCTION_TOPOLOGY.md`
4. `PRODUCTION_TRUTH_AUDIT_2026-04-07.md`
5. role-specific prompt / SOP

## Required Assertions Before Action
An agent must be able to answer these correctly before deploy or infra work:
- What is the live API service name?
- What is the canonical runtime root?
- Which host runs NGINX?
- Which host runs FastAPI?
- What is the current NGINX upstream target?
- Which deployment scripts are canonical and which are legacy?

## Required Behavior
- Do not assume old docs are true.
- Do not trust file names like `deploy` or `production` automatically.
- Re-verify live truth when touching infrastructure.
- Mark legacy artifacts clearly instead of letting them silently coexist.
- Prefer private-IP internal routing inside AWS when architecture supports it.

## Escalation Rule
If a prompt, script, or config conflicts with verified live reality:
1. stop automation
2. document the conflict
3. update the truth docs
4. only then continue

## Marvin Authority
Marvin is the canonical truth reconciler for infrastructure drift until this system is fully normalized.

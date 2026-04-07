# Internal Agents Boot Order

Last updated: 2026-04-07
Author: Marvin, COO

## Purpose
Define the safe wake-up order for internal BlueSoap agents after production truth normalization.

## Boot order
1. Delta
   - reason: deployment, infrastructure, service truth
2. Zeta
   - reason: data, CRM, systems structure
3. Kappa
   - reason: revenue, treasury, payment rails
4. Gamma
   - reason: communications and scheduling
5. Muse
   - reason: client-facing polish and design system alignment
6. Sigma
   - reason: SOP and documentation reinforcement
7. Alpha / Beta / others
   - after infra and revenue truth is stable

## Mandatory grounding for all agents
Every agent must read:
- `FOUNDATIONAL_TRUTH.md`
- `AGENT_ONBOARDING_TRUTH_PROTOCOL.md`

## Rule
No agent should act on inherited assumptions from Antigravity-era files when a verified truth doc exists.

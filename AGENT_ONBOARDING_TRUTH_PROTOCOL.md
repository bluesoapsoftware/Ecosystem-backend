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

## Container Registry Strategy (Multi-Cloud Freedom)
To ensure portability and resilience, BlueSoap employs a multi-registry strategy:

1.  **Primary Cloud-Native Registries:**
    *   **AWS ECR:** Used for Docker images primarily destined for AWS deployments (e.g., ECS, EKS).
    *   **Google Cloud Artifact Registry (GAR):** Will be used for Docker images primarily destined for Google Cloud deployments (e.g., GKE).
    *   **Principle:** Leverage the native security, performance, and integration benefits of each cloud provider's registry.

2.  **Cross-Cloud Image Management (Future Consideration):**
    *   Initially, images will be built once and pushed to the relevant cloud-native registry based on the target deployment environment.
    *   As the system matures, we may explore neutral secondary registries (e.g., Docker Hub private repositories) or advanced replication strategies for comprehensive cross-cloud image availability, but this is not an immediate priority due to operational overhead.
    *   **Principle:** Build once, deploy anywhere (via appropriate registry pushes).

## Required Assertions Before Action
An agent must be able to answer these correctly before deploy or infra work:
- What is the live API service name?
- What is the canonical runtime root?
- Which host runs NGINX?
- Which host runs FastAPI?
- What is the current NGINX upstream target?
- Which deployment scripts are canonical and which are legacy?
- What is the designated container registry for the target cloud environment (e.g., ECR for AWS, GAR for Google Cloud)?

## Required Behavior
- Do not assume old docs are true.
- Do not trust file names like `deploy` or `production` automatically.
- Re-verify live truth when touching infrastructure.
- Mark legacy artifacts clearly instead of letting them silently coexist.
- Prefer private-IP internal routing inside AWS when architecture supports it.
- Always push Docker images to the *appropriate* cloud-native container registry for the target deployment.

## Escalation Rule
If a prompt, script, or config conflicts with verified live reality:
1. stop automation
2. document the conflict
3. update the truth docs
4. only then continue

## Marvin Authority
Marvin is the canonical truth reconciler for infrastructure drift until this system is fully normalized.

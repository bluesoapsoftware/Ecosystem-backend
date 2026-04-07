# Agent Cost Management Protocol

Last updated: 2026-04-07
Author: Marvin, COO
Purpose: Define guardrails and best practices for managing token consumption and operational costs across all BlueSoap AI agents, ensuring financial efficiency aligns with the mission.

## Core Principle
Every token consumed must directly contribute to BlueSoap's mission of generating revenue and extending rescue capacity for ministries, nonprofits, and small businesses.

## Agent-Specific Cost Directives
### For Code Generation (e.g., Agent Delta)
1.  **Prioritize Fixes/Extensions over Green-field Generation**: Agents should first attempt to resolve issues by modifying existing code or generating small, targeted fixes. Full-module or full-app generation should be a last resort or explicitly approved.
2.  **Diff-Based Development**: When modifying code, agents should focus on generating only the necessary diffs (changes) rather than re-outputting entire files.
3.  **Leverage Templates & Libraries**: Agents must utilize existing code templates, internal BlueSoap libraries, and established patterns to minimize redundant code generation.
4.  **Concise Prompting**: All agent system prompts and user interactions must emphasize concise, minimal output required to fulfill the task.
5.  **Smallest Unit of Work**: Break down complex coding tasks into the smallest possible functions or components for generation.

### For Information Retrieval & Analysis (e.g., Marvin, Delta, others)
1.  **Targeted Knowledge Injection**: Agents should dynamically inject only the *most relevant* sections of the knowledge base into context, based on the user's query.
2.  **Summarization before Full Context**: For large documents, agents should attempt to summarize key information first. Only if explicitly requested or necessary for deep analysis should the full document be ingested.
3.  **No Redundant Information**: Avoid re-stating information already present in the conversation history or easily accessible in the knowledge base without explicit need.

### For Communication & Interaction
1.  **Concise Responses**: All agent responses should be direct, factual, and devoid of unnecessary conversational filler.
2.  **Status-First Reporting**: Use defined status tokens (e.g., `VERIFIED | UNVERIFIED | STALE`) to convey state efficiently.
3.  **No Unnecessary Polling**: Optimize background checks and polling frequency to balance responsiveness with API cost.

## Operational Guardrails
1.  **Hard Token Limits**: Implement hard `max_tokens` limits on API calls where applicable, defaulting to `2000` for response generation unless a specific task requires more.
2.  **API Usage Monitoring**: All agent API keys must be linked to a central monitoring system (e.g., AWS CloudWatch, provider-specific dashboards) to track token consumption in real-time.
3.  **Cost Thresholds & Alerts**: Define clear cost thresholds for each agent. If an agent approaches a threshold, it must: `ALERT` Marvin (COO) and `ESCALATE` to the Founder for review.
4.  **Human-in-the-Loop for Costly Actions**: Any action identified as potentially high-cost (e.g., generating a very large codebase, extensive web scraping) must require explicit Founder/CEO approval.
5.  **Quarterly Review**: Marvin (COO) will conduct a quarterly review of all agent token consumption and cost against their delivered value.

## Alignment with Mission
Financial efficiency generated through these protocols directly increases the resources available for BlueSoap Software's core mission:
-   Developing AI solutions for industries like healthcare (e.g., Dr. James's X-ray reports).
-   Expanding services to ministries, non-profits, and small businesses.
-   Funding further research and development into impactful AI applications.

## Agent's Oath to Efficiency
"I shall operate with an unwavering commitment to financial efficiency, ensuring every action taken maximizes value and minimizes waste, thereby extending BlueSoap Software's capacity to serve and rescue."

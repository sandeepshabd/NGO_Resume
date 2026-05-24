# Architecture

SkillBridge AI uses a main orchestrator plus specialist agents. Every agent is a separately
deployable Cloud Run service with an A2A-style Agent Card and a single task API.

```mermaid
flowchart TD
  UI[User app] --> API[API Gateway or Load Balancer]
  API --> Main[Orchestrator Agent]
  Main --> Registry[Agent Registry from cards]
  Main --> Resume[Resume Parser Agent]
  Main --> Skill[Skill Graph Agent]
  Main --> Jobs[Job Market Agent]
  Main --> Match[Matching Agent]
  Main --> Learn[Learning Path Agent]
  Main --> Interview[Interview Coach Agent]
  Main --> Report[Report Writer Agent]
  Main --> Ops[Ops Auto-Correction Agent]
  Resume --> Storage[MCP storage/document tools]
  Jobs --> BigQuery[MCP job market/BigQuery tools]
  Ops --> Monitoring[Cloud Logging and Monitoring]
```

## Boundaries

- A2A is used for agent-to-agent task delegation.
- MCP is used for agent-to-tool and agent-to-data access.
- The orchestrator should not directly access specialist data tools unless there is a product
  reason to make that capability part of orchestration.
- Each agent should get its own service account in production.

## Agent Contract

Each service exposes:

- `GET /healthz`
- `GET /.well-known/agent-card.json`
- `POST /tasks`

`POST /tasks` accepts `TaskRequest` and returns `TaskResponse` from
`packages/skillbridge_common/schemas.py`.

## Operations Auto-Correction

The ops agent diagnoses alerts and proposes actions. Low-risk actions can be automated later.
Medium and high-risk actions should flow through approval.

Initial safe actions:

- open an incident ticket
- switch to a fallback model
- pause queue consumers
- roll back Cloud Run traffic after approval
- create a configuration PR

Blocked without approval:

- IAM changes
- secret changes
- deleting data
- production database migrations
- user-impacting recommendation policy changes


# Agent Deployment Model

For the POC, SkillBridge uses one shared runtime identity and separate Cloud Run services.

## Recommended POC Shape

```text
skillbridge-web
  -> skillbridge-web-api-agent
    -> skillbridge-orchestrator-agent
      -> skillbridge-resume-parser-agent
      -> skillbridge-skill-graph-agent
      -> skillbridge-learning-path-agent
      -> skillbridge-report-writer-agent
      -> skillbridge-ops-autocorrect-agent
      -> optional MCP tool services
```

Each service is deployed separately, scales independently, and can be removed or replaced without
changing the frontend. The orchestrator decides what to call by reading `AGENT_REGISTRY_JSON`, which
contains the active Agent Cards.

## Shared Service Account

All agent services can run as:

```text
skillbridge-agent@PROJECT_ID.iam.gserviceaccount.com
```

This is acceptable for the POC because you are the developer of all agents and want easy
operations. It also keeps Cloud Run IAM and Secret Manager setup simple.

Tradeoff: Cloud Logging can still show which Cloud Run service handled an action, but IAM will not
distinguish agent-by-agent privileges. In production, we can split service accounts later for
stronger least-privilege boundaries.

## Loose Binding

Loose binding is achieved through three layers:

- Separate Cloud Run service per agent
- A2A Agent Cards in `AGENT_REGISTRY_JSON`
- MCP tool servers behind agent-specific tool adapters

To remove an agent:

1. Remove its card from `AGENT_REGISTRY_JSON`.
2. Update the orchestrator service env var.
3. Delete or pause the Cloud Run service if desired.

To add an agent:

1. Deploy the new Cloud Run service.
2. Confirm `/.well-known/agent-card.json`.
3. Add the card to `AGENT_REGISTRY_JSON`.
4. The orchestrator can start routing to it without frontend changes.

## MCP Servers

Agents are not themselves MCP servers by default. They are A2A agents that can call MCP tool
servers. For example:

```text
resume-parser-agent -> mcp-storage-server / mcp-document-server
job-market-agent    -> mcp-usajobs-server
ops-autocorrect     -> mcp-observability-server
```

For the first demo, tool access is implemented through internal adapters. MCP servers can be
deployed as separate Cloud Run services later, still using the same shared service account if we
want to keep operations simple.


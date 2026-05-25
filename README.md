# SkillBridge AI

SkillBridge AI is a Google Cloud-ready, loosely coupled agent system for resume analysis,
skill-gap mapping, job matching, learning-path generation, interview coaching, reporting,
and operations auto-correction.

The code is scaffolded for Cloud Run services. Each agent exposes:

- `GET /healthz`
- `GET /.well-known/agent-card.json`
- `POST /tasks`

The orchestrator discovers specialist agents from A2A-style Agent Cards and calls them only
through their public task contract. Specialist agents use MCP-style tool adapters for data,
documents, storage, job market sources, and operations actions.

## Repo Layout

```text
agents/                 Cloud Run service entrypoints
apps/web/               Next.js POC frontend
packages/               Shared A2A, MCP, schemas, logging, and security code
infra/                  Terraform and Cloud Build templates
docs/                   Architecture, deployment, and operations notes
```

See `docs/agent-deployment-model.md` for the POC deployment model: separate Cloud Run services,
one shared runtime service account, A2A Agent Card registry, and optional MCP tool services.

## Local Commands

These commands are provided for later. They have not been run by Codex.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn agents.orchestrator.main:app --reload --port 8080
uvicorn agents.web_api.main:app --reload --port 8081
```

## Deployment

Deployment is intentionally separated from this scaffold. The next step is to choose the
Google Cloud project, region, service names, and data stores, then apply the templates in
`infra/`.

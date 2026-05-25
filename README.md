# SkillBridge AI

SkillBridge AI is a Google Cloud-ready, loosely coupled agent system for resume analysis,
skill-gap mapping, job matching, learning-path generation, interview coaching, reporting,
and operations auto-correction.

The current repository is ready for an architecture demo: each core agent can run as a separate
Cloud Run service, the public web API can call the deployed orchestrator, and the orchestrator can
discover specialist agents by A2A-style Agent Cards.

Each agent exposes:

- `GET /healthz`
- `GET /readyz`
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

## Architecture

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

The frontend uses Server-Sent Events from `web-api` to show the user what the main agent is doing.
The web API stores demo state in memory for the POC and can later be backed by Firebase Auth,
Firestore, and Cloud Storage. The job API path uses USAJOBS when credentials are configured and a
demo fallback otherwise.

## Agents

| Agent | Service Module | Responsibility | Main Skill |
| --- | --- | --- | --- |
| Web API | `agents.web_api.main` | Public API for demo login, resume upload, chat, dashboard, job search, and SSE status | `n/a` |
| Orchestrator | `agents.orchestrator.main` | Main planning agent; creates workflow plan and routes work to specialists via A2A registry | `career_readiness_workflow` |
| Resume Parser | `agents.resume_parser.main` | Extracts profile facts, contact signals, education, projects, skills, and role hints from resume text | `parse_resume` |
| Skill Graph | `agents.skill_graph.main` | Normalizes skills and compares candidate skills to target-role baselines | `gap_analysis`, `normalize_skills` |
| Learning Path | `agents.learning_path.main` | Converts skill gaps into week-by-week practice plan and portfolio evidence | `build_learning_path` |
| Report Writer | `agents.report_writer.main` | Produces user/advisor-facing readiness report and next actions | `write_career_report` |
| Ops Auto-Correct | `agents.ops_autocorrect.main` | Diagnoses alerts and proposes safe remediation actions with approval gates | `diagnose_alert` |
| Job Market | `agents.job_market.main` | Placeholder specialist for market demand; current Web API directly calls USAJOBS adapter | `job_market_scan` |

Shared packages:

- `skillbridge_common.schemas`: task, agent card, workflow, and remediation contracts
- `skillbridge_common.a2a`: agent registry and A2A task client
- `skillbridge_common.orchestrator_client`: local/remote orchestrator switch
- `skillbridge_common.career`: deterministic resume/skill/learning/report logic
- `skillbridge_common.jobs`: USAJOBS client and demo fallback
- `skillbridge_common.logging`: structured workflow logging
- `skillbridge_common.privacy`: PII redaction and stable user hashing
- `skillbridge_common.llm`: LLM gateway, disabled by default for low-cost POC

## Production-Readiness Notes

The POC intentionally keeps operations simple, but the code now includes production-facing seams:

- separate Cloud Run services for agents
- shared runtime service account for POC, splittable later per agent
- Secret Manager for the shared agent token
- non-root Python container runtime
- `.dockerignore` to keep build context small
- `/healthz` and `/readyz` endpoints
- structured logs with workflow, trace, step, event, status, and duration
- PII redaction before logging
- `min-instances=0` and `max-instances=1` demo deployment defaults
- remote orchestrator support through `ORCHESTRATOR_URL`
- A2A registry through `AGENT_REGISTRY_JSON`

Before production, replace in-memory state with Firebase/Firestore/Cloud Storage, make Cloud Run
agent ingress private, verify Firebase ID tokens in `web-api`, and consider one service account per
agent for strict least privilege.

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

The architecture demo deploys each agent as a separate Cloud Run service while using one shared
runtime service account for easier POC operations. Replace placeholder values before running.

### 1. Configure Project

```bash
export PROJECT_ID="your-project-id"
export REGION="us-south1"
export AGENT_SA="skillbridge-agent@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"
```

Enable required APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  monitoring.googleapis.com \
  pubsub.googleapis.com
```

### 2. Create Shared Runtime Identity

```bash
gcloud iam service-accounts create skillbridge-agent \
  --display-name="SkillBridge Agent Runtime"
```

Create the shared agent-call secret:

```bash
printf "replace-with-a-random-shared-token" | \
gcloud secrets create skillbridge-agent-token \
  --data-file=-
```

Allow the shared runtime identity to read it:

```bash
gcloud secrets add-iam-policy-binding skillbridge-agent-token \
  --member="serviceAccount:${AGENT_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

Allow the runtime identity to export traces:

```bash
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${AGENT_SA}" \
  --role="roles/cloudtrace.agent"
```

### 3. Create Artifact Registry

```bash
gcloud artifacts repositories create skillbridge \
  --repository-format=docker \
  --location="${REGION}" \
  --description="SkillBridge AI images"
```

If the repository already exists, continue.

### 4. Deploy Specialist Agents

Run from the repository root:

```bash
for SERVICE in resume-parser skill-graph learning-path report-writer ops-autocorrect; do
  MODULE=$(echo "${SERVICE}" | sed 's/-/_/g')
  gcloud run deploy "skillbridge-${SERVICE}-agent" \
    --source . \
    --region "${REGION}" \
    --allow-unauthenticated \
    --service-account "${AGENT_SA}" \
    --set-env-vars "AGENT_MODULE=agents.${MODULE}.main" \
    --set-secrets "SKILLBRIDGE_AGENT_TOKEN=skillbridge-agent-token:latest" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 1
done
```

List service URLs:

```bash
gcloud run services list --region "${REGION}"
```

### 5. Build Agent Registry

Generate `agent-registry.json` from deployed Cloud Run services:

```bash
python3 scripts/generate_agent_registry.py "${REGION}" > agent-registry.json
python3 -m json.tool agent-registry.json
```

Or create it manually with deployed service URLs:

```json
[
  {
    "name": "resume-parser-agent",
    "description": "Extracts structured experience, education, projects, and skills from resumes.",
    "url": "https://skillbridge-resume-parser-agent-PROJECT_NUMBER.REGION.run.app",
    "skills": [{"id": "parse_resume", "name": "Parse Resume", "description": "Parses resume text."}]
  },
  {
    "name": "skill-graph-agent",
    "description": "Normalizes skills and maps skill gaps against target roles.",
    "url": "https://skillbridge-skill-graph-agent-PROJECT_NUMBER.REGION.run.app",
    "skills": [{"id": "gap_analysis", "name": "Skill Gap Analysis", "description": "Compares skills to role baseline."}]
  },
  {
    "name": "learning-path-agent",
    "description": "Builds practical learning plans from skill gaps.",
    "url": "https://skillbridge-learning-path-agent-PROJECT_NUMBER.REGION.run.app",
    "skills": [{"id": "build_learning_path", "name": "Build Learning Path", "description": "Creates a roadmap."}]
  },
  {
    "name": "report-writer-agent",
    "description": "Turns agent outputs into user-facing career plans.",
    "url": "https://skillbridge-report-writer-agent-PROJECT_NUMBER.REGION.run.app",
    "skills": [{"id": "write_career_report", "name": "Write Career Report", "description": "Creates a career report."}]
  }
]
```

### 6. Deploy Orchestrator

```bash
python3 - <<'PY'
import json
from pathlib import Path

registry = json.loads(Path("agent-registry.json").read_text())
registry_string = json.dumps(registry).replace("'", "''")
Path("orchestrator-env.yaml").write_text(
    "AGENT_MODULE: 'agents.orchestrator.main'\n"
    f"AGENT_REGISTRY_JSON: '{registry_string}'\n"
)
PY

gcloud run deploy skillbridge-orchestrator-agent \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --service-account "${AGENT_SA}" \
  --env-vars-file orchestrator-env.yaml \
  --set-secrets "SKILLBRIDGE_AGENT_TOKEN=skillbridge-agent-token:latest" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1
```

Save the orchestrator URL:

```bash
export ORCHESTRATOR_URL="$(gcloud run services describe skillbridge-orchestrator-agent \
  --region "${REGION}" \
  --format='value(status.url)')"
```

### 7. Deploy Web API

```bash
gcloud run deploy skillbridge-web-api-agent \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --service-account "${AGENT_SA}" \
  --set-env-vars "AGENT_MODULE=agents.web_api.main,ORCHESTRATOR_URL=${ORCHESTRATOR_URL},FIREBASE_AUTH_ENABLED=false,CORS_ALLOW_ORIGINS=*" \
  --set-secrets "SKILLBRIDGE_AGENT_TOKEN=skillbridge-agent-token:latest" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1
```

Save the Web API URL:

```bash
export WEB_API_URL="$(gcloud run services describe skillbridge-web-api-agent \
  --region "${REGION}" \
  --format='value(status.url)')"
```

### 8. Deploy Frontend

```bash
cd apps/web

export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/skillbridge/skillbridge-web:latest"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL="${WEB_API_URL}" \
  -t "${IMAGE}" \
  .

docker push "${IMAGE}"

gcloud run deploy skillbridge-web \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1
```

### 9. Smoke Test

Open the frontend URL and use:

```text
Target role: data analyst
Location: Texas

Resume:
Jane Doe
jane@example.com
3 years building Python SQL Excel dashboards.
Built portfolio project for stakeholder reporting.
Bachelor of Science, Example University
```

Expected result:

- demo login works
- resume upload works
- chat streams agent status via SSE
- dashboard shows skill gaps and learning path
- job cards appear from USAJOBS or demo fallback

## Diagnose With Google Cloud

### Service Health

```bash
for SVC in \
  skillbridge-resume-parser-agent \
  skillbridge-skill-graph-agent \
  skillbridge-learning-path-agent \
  skillbridge-report-writer-agent \
  skillbridge-ops-autocorrect-agent \
  skillbridge-orchestrator-agent \
  skillbridge-web-api-agent
do
  URL=$(gcloud run services describe "$SVC" --region "${REGION}" --format='value(status.url)')
  echo "== $SVC =="
  curl -s "$URL/healthz"
  echo
done
```

### Agent Cards

```bash
URL=$(gcloud run services describe skillbridge-orchestrator-agent \
  --region "${REGION}" \
  --format='value(status.url)')
curl -s "$URL/.well-known/agent-card.json" | python3 -m json.tool
```

### Web API Smoke Test

```bash
curl -s -X POST "$WEB_API_URL/auth/demo-login" | python3 -m json.tool

cat > /tmp/demo-resume.txt <<'EOF'
Jane Doe
jane@example.com
3 years building Python SQL Excel dashboards.
Built portfolio project for stakeholder reporting.
Bachelor of Science, Example University
EOF

curl -s -X POST "$WEB_API_URL/api/resumes" \
  -H "Authorization: Bearer demo-user" \
  -F "file=@/tmp/demo-resume.txt" | python3 -m json.tool

curl -N "$WEB_API_URL/api/chat/events?message=What%20jobs%20fit%20me&target_role=data%20analyst&location=Texas&user_id=demo-user"
```

### Recent Cloud Run Logs

```bash
gcloud logging read \
  'resource.type="cloud_run_revision"
   resource.labels.service_name="skillbridge-web-api-agent"' \
  --limit=50 \
  --format=json
```

Useful filters:

```text
jsonPayload.event_type="chat_workflow_completed"
jsonPayload.event_type="workflow_planned"
jsonPayload.event_type="agent_step_failed"
jsonPayload.status="failed"
severity>=ERROR
```

### Trace UI (Service-to-Service Flow)

The application emits OpenTelemetry traces to Google Cloud Trace. This is the
recommended UI for viewing request flow across Cloud Run services.

Open:

```text
Google Cloud Console -> Observability -> Trace
```

Usage:

- set time range to `Last 1 hour`
- open a trace and inspect the waterfall path and per-hop latency
- correlate trace logs in Logs Explorer with:

```text
resource.type="cloud_run_revision"
trace="projects/PROJECT_ID/traces/TRACE_ID"
```

Notes:

- Cloud Trace shows application request flow, not packet-level network flow.
- Timestamps in the UI follow the browser/account timezone setting.

### Cloud Armor Scope

Cloud Armor is not an application-code feature. It is configured at the edge
through Google Cloud infrastructure:

- External HTTP(S) Load Balancer
- backend service mapping to Cloud Run
- security policy rules attached to the backend service

For this reason, Cloud Armor rollout is an infrastructure deployment change
(recommended via Terraform), not a Python or Next.js code change.

Examples:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision"
   jsonPayload.event_type="agent_step_failed"' \
  --limit=20 \
  --format="table(timestamp,resource.labels.service_name,jsonPayload.step_id,jsonPayload.status,jsonPayload.error_type)"

gcloud logging read \
  'resource.type="cloud_run_revision"
   jsonPayload.workflow_id:*' \
  --limit=20 \
  --format="table(timestamp,resource.labels.service_name,jsonPayload.event_type,jsonPayload.step_id,jsonPayload.status,jsonPayload.duration_ms)"
```

The logging layer redacts resume text, messages, emails, phone numbers, filenames, tokens, and raw
user identifiers. You should see counts, statuses, trace IDs, and hashed identifiers instead of PII.

### Metrics In Console

In Google Cloud Console:

1. Go to **Cloud Run**.
2. Select a SkillBridge service.
3. Open **Metrics**.
4. Watch request count, latency, 4xx/5xx errors, container startup latency, and instance count.
5. Open **Logs** from the same service and filter by `jsonPayload.event_type`.

For dashboard/alert setup, start with:

- request error rate for `skillbridge-web-api-agent`
- p95 request latency for `skillbridge-orchestrator-agent`
- count of `jsonPayload.event_type="agent_step_failed"`
- count of `jsonPayload.status="failed"`

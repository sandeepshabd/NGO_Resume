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

Create `agent-registry.json` with deployed service URLs:

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
export AGENT_REGISTRY_JSON="$(cat agent-registry.json)"

gcloud run deploy skillbridge-orchestrator-agent \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --service-account "${AGENT_SA}" \
  --set-env-vars "AGENT_MODULE=agents.orchestrator.main,AGENT_REGISTRY_JSON=${AGENT_REGISTRY_JSON}" \
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

cat > .env.production <<EOF
NEXT_PUBLIC_API_BASE_URL=${WEB_API_URL}
EOF

gcloud run deploy skillbridge-web \
  --source . \
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

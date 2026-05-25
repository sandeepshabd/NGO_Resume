# Deployment Notes

This repository is ready for Google Cloud deployment planning, but no deployment has been run.

## Decisions Needed

- `GCP_PROJECT_ID`
- `GCP_REGION`
- public domain and ingress policy
- Firestore vs AlloyDB for user workflow state
- BigQuery datasets for job market analytics
- Vertex AI model choice
- whether agents are public, internal-only, or behind API Gateway
- Firebase project and web config
- USAJOBS API email and key

## Build Pattern

All services use the root `Dockerfile`. The runtime module is selected with `AGENT_MODULE`.

Examples:

```text
agents.orchestrator.main
agents.resume_parser.main
agents.skill_graph.main
agents.job_market.main
agents.matching.main
agents.learning_path.main
agents.interview_coach.main
agents.report_writer.main
agents.ops_autocorrect.main
agents.web_api.main
```

## POC Frontend

The Next.js app lives in `apps/web`. Configure:

```text
NEXT_PUBLIC_API_BASE_URL=https://skillbridge-web-api-...run.app
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
```

For the lowest-cost demo, keep Firebase auth disabled on the API and use `/auth/demo-login`.
After the Firebase project is selected, turn on `FIREBASE_AUTH_ENABLED=true` and replace the POC
token verifier with Firebase Admin ID-token verification.

## USAJOBS

The web API calls USAJOBS when these are configured:

```text
USAJOBS_EMAIL=...
USAJOBS_API_KEY=...
```

Without those values, it returns demo jobs so the dashboard still works.

## Terraform

The Terraform template creates:

- Artifact Registry repository
- Pub/Sub remediation topic
- shared starter service account
- Cloud Run services for each agent

The image references are placeholders until the build pipeline is finalized.

## Agent Registry

For the first deployment, provide `AGENT_REGISTRY_JSON` to the orchestrator with the deployed
Agent Cards for specialist services. Later, replace this with a small registry service backed by
Firestore.

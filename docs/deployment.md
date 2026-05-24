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
```

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


# Operations

SkillBridge agents emit structured JSON logs. Cloud Logging can turn these logs into metrics,
and Cloud Monitoring can route alerts to the ops auto-correction workflow.

## Required Log Fields

- `agent`
- `task_id`
- `trace_id`
- `workflow_id`
- `step_id`
- `event_type`
- `status`
- `duration_ms`
- `message`
- `status`, when a task completes

## Privacy Rules

Logs must never include raw resume text, chat message text, auth tokens, API keys, email addresses,
phone numbers, candidate names, filenames, or un-hashed user identifiers. The shared logging helper
redacts sensitive keys and hashes user identifiers before writing structured events.

Safe fields for debugging:

- workflow and task ids
- trace ids that are generated or hashed
- target role and location
- agent and step names
- status and duration
- payload key names, never payload values
- counts such as skill count, gap count, job result count, and bytes received

## Alert Flow

1. Cloud Run emits request and application logs.
2. Cloud Logging creates log-based metrics for task failures.
3. Cloud Monitoring alert policies detect high error rate or latency.
4. Alert notification routes to Pub/Sub.
5. The ops auto-correction agent diagnoses the alert.
6. Safe remediation is applied or an approval request is created.

## First SLOs

- API availability: 99.5 percent monthly
- agent task completion rate: 98 percent daily
- p95 orchestrator latency: under 8 seconds for non-document workflows
- p95 specialist latency: under 5 seconds

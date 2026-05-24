# Operations

SkillBridge agents emit structured JSON logs. Cloud Logging can turn these logs into metrics,
and Cloud Monitoring can route alerts to the ops auto-correction workflow.

## Required Log Fields

- `agent`
- `task_id`
- `trace_id`
- `message`
- `status`, when a task completes

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


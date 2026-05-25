terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_artifact_registry_repository" "skillbridge" {
  location      = var.region
  repository_id = "skillbridge"
  description   = "SkillBridge AI agent images"
  format        = "DOCKER"
}

resource "google_pubsub_topic" "remediation_events" {
  name = "skillbridge-remediation-events"
}

resource "google_service_account" "agent" {
  account_id   = "skillbridge-agent"
  display_name = "SkillBridge agent runtime"
}

resource "google_project_iam_member" "agent_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent.email}"
}

resource "google_project_iam_member" "agent_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.agent.email}"
}

resource "google_project_iam_member" "agent_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.agent.email}"
}

locals {
  agents = {
    orchestrator       = "agents.orchestrator.main"
    resume_parser      = "agents.resume_parser.main"
    skill_graph        = "agents.skill_graph.main"
    job_market         = "agents.job_market.main"
    matching           = "agents.matching.main"
    learning_path      = "agents.learning_path.main"
    interview_coach    = "agents.interview_coach.main"
    report_writer      = "agents.report_writer.main"
    ops_autocorrect    = "agents.ops_autocorrect.main"
    web_api            = "agents.web_api.main"
  }
}

resource "google_cloud_run_v2_service" "agents" {
  for_each = local.agents

  name     = "skillbridge-${replace(each.key, "_", "-")}-agent"
  location = var.region

  template {
    service_account = google_service_account.agent.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/skillbridge/${each.key}:latest"

      env {
        name  = "AGENT_MODULE"
        value = each.value
      }

      env {
        name  = "PUBSUB_REMEDIATION_TOPIC"
        value = google_pubsub_topic.remediation_events.name
      }

      env {
        name  = "AGENT_REGISTRY_JSON"
        value = var.agent_registry_json
      }

      env {
        name  = "ORCHESTRATOR_URL"
        value = var.orchestrator_url
      }

      env {
        name  = "CORS_ALLOW_ORIGINS"
        value = var.cors_allow_origins
      }

      env {
        name = "SKILLBRIDGE_AGENT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = var.agent_token_secret_id
            version = "latest"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}

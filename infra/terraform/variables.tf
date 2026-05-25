variable "project_id" {
  type        = string
  description = "Google Cloud project id."
}

variable "region" {
  type        = string
  description = "Google Cloud region for Cloud Run and Artifact Registry."
  default     = "us-central1"
}

variable "agent_token_secret_id" {
  type        = string
  description = "Secret Manager secret id containing the shared agent token."
  default     = "skillbridge-agent-token"
}

variable "agent_registry_json" {
  type        = string
  description = "A2A Agent Card registry JSON passed to the orchestrator."
  default     = "[]"
}

variable "orchestrator_url" {
  type        = string
  description = "Cloud Run URL for the deployed orchestrator service. Used by web-api."
  default     = ""
}

variable "cors_allow_origins" {
  type        = string
  description = "Comma-separated frontend origins allowed to call web-api."
  default     = "*"
}

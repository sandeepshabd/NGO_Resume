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


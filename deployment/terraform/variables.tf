variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The default region for resources"
  type        = string
  default     = "us-central1"
}

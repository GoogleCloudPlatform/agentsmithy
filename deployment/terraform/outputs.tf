output "project_id" {
  description = "The Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "The region where resources are deployed"
  value       = var.region
}

output "agent_service_account_email" {
  description = "The email of the service account created for the agent"
  value       = google_service_account.agent_sa.email
}

output "artifact_registry_repository_id" {
  description = "The ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.agent_repo.id
}

output "default_data_bucket_name" {
  description = "The name of the GCS default data bucket"
  value       = google_storage_bucket.default_data_bucket.name
}

output "product_ad_generation_bucket_name" {
  description = "The name of the GCS bucket for product ad generation"
  value       = google_storage_bucket.product_ad_generation_bucket.name
}

output "campaign_manager_bucket_name" {
  description = "The name of the GCS bucket for campaign manager"
  value       = google_storage_bucket.campaign_manager_bucket.name
}

output "meeting_intelligence_bucket_name" {
  description = "The name of the GCS bucket for meeting intelligence"
  value       = google_storage_bucket.meeting_intelligence_bucket.name
}

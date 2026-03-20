# 3. Artifact Registry for Cloud Run Images
resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = var.ar_repository_id
  description   = var.ar_description
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis]
}

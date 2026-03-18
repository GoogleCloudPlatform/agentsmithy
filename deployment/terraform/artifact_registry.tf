# 3. Artifact Registry for Cloud Run Images
resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = "agent-bar-v2-repo"
  description   = "Docker repository for Agent Bar v2 images"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis]
}

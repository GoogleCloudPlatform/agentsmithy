# 4. Service Account for the Agent
resource "google_service_account" "agent_sa" {
  account_id   = "agent-bar-v2-sa"
  display_name = "Agent Bar v2 Service Account"
  depends_on   = [google_project_service.enabled_apis]
}

# 5. IAM Roles for the Service Account
resource "google_project_iam_member" "agent_sa_roles" {
  for_each = toset(local.agent_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.agent_sa.email}"
}

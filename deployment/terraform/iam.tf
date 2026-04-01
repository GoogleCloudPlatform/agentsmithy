# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# 4. Service Account for the Agent
resource "google_service_account" "agent_sa" {
  account_id   = var.sa_account_id
  display_name = var.sa_display_name
  depends_on   = [google_project_service.enabled_apis]
}

# 5. IAM Roles for the Service Account
resource "google_project_iam_member" "agent_sa_roles" {
  for_each = toset(local.agent_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Get project details
data "google_project" "project" {}

# 6. IAM Roles for default Compute Engine SA for Cloud Build
resource "google_project_iam_member" "compute_sa_build_roles" {
  for_each   = toset(local.build_service_account_roles)
  project    = var.project_id
  role       = each.key
  member     = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  depends_on = [google_project_service.enabled_apis]
}

# 7. IAM Roles for default Cloud Build SA
resource "google_project_iam_member" "cloudbuild_sa_roles" {
  for_each   = toset(local.build_service_account_roles)
  project    = var.project_id
  role       = each.key
  member     = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  depends_on = [google_project_service.enabled_apis]
}

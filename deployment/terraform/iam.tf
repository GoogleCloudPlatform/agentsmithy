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

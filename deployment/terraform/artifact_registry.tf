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

# 3. Artifact Registry for Cloud Run Images
resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = "agent-bar-v2-repo"
  description   = "Docker repository for Agent Bar v2 images"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_apis]
}

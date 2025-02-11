# Copyright 2025 Google LLC
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
resource "google_artifact_registry_repository" "my-repo" {
  location      = var.region
  repository_id = local.artifact_registry_repo_name
  description   = "Repo for Generative AI applications"
  format        = "DOCKER"
  project       = var.prod_project_id
  depends_on    = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}
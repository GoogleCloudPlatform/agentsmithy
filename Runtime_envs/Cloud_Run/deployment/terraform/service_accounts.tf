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
resource "google_service_account" "cicd_runner_sa" {
  account_id   = local.cicd_runner_sa_name
  display_name = "CICD Runner SA"
  project      = var.prod_project_id
  depends_on   = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_service_account" "cloud_run_app_sa" {
  for_each = local.deploy_project_ids

  account_id   = local.cloud_run_app_sa_name
  display_name = "Cloud Run Generative AI app SA"
  project      = each.value
  depends_on   = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

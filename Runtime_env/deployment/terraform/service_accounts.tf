# Copyright 2025 Google LLC. All Rights Reserved.
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
resource "google_service_account" "cloud_run_app_sa" {
  for_each = local.deploy_project_ids

  account_id   = local.cloud_run_app_sa_name
  display_name = "Cloud Run Generative AI app SA"
  project      = each.value
  depends_on   = [resource.google_project_service.shared_services]
}

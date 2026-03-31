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

# 1. Default Data Bucket
resource "google_storage_bucket" "default_data_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_default_data}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 2. Sub-agent requirements (cross_industry/product_ad_generation)
resource "google_storage_bucket" "product_ad_generation_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_product_ad_generation}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 3. Campaign Manager Sub-agent
resource "google_storage_bucket" "campaign_manager_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_campaign_manager}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 4. Meeting Intelligence Sub-agent
resource "google_storage_bucket" "meeting_intelligence_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_meeting_intelligence}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 5. Macroeconomics Bucket
resource "google_storage_bucket" "macroeconomics_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_macroeconomics}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.enabled_apis]
}

# 6. Economics Sub-agent Data
resource "google_storage_bucket_object" "economics_world_bank_data" {
  name   = "fsi/economics/data/world_bank_data_2025.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/holistic_investment_strategy/economics/data/world_bank_data_2025.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

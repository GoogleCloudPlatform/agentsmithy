# Copyright 2026 Google LLC
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

  depends_on = [time_sleep.wait_for_api_enablement]
}

# 2. Sub-agent requirements (cross_industry/product_ad_generation)
resource "google_storage_bucket" "product_ad_generation_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_product_ad_generation}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [time_sleep.wait_for_api_enablement]
}

# 3. Campaign Manager Sub-agent
resource "google_storage_bucket" "campaign_manager_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_campaign_manager}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [time_sleep.wait_for_api_enablement]
}

# 4. Meeting Intelligence Sub-agent
resource "google_storage_bucket" "meeting_intelligence_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_meeting_intelligence}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [time_sleep.wait_for_api_enablement]
}

# 5. Macroeconomics Bucket
resource "google_storage_bucket" "macroeconomics_bucket" {
  name          = "${var.project_id}${var.bucket_suffix_macroeconomics}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [time_sleep.wait_for_api_enablement]
}

# 6. Economics Sub-agent Data
resource "google_storage_bucket_object" "economics_world_bank_data" {
  name   = "fsi/economics/data/world_bank_data_2025.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/holistic_investment_strategy/economics/data/world_bank_data_2025.csv"
  bucket = google_storage_bucket.macroeconomics_bucket.name
}

# 7. Retail Sub-agent Sample Data
resource "google_storage_bucket_object" "retail_products_data" {
  name   = "retail/data/products.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/retail/intelligent_inventory_manager/data/products.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "retail_stores_data" {
  name   = "retail/data/stores.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/retail/intelligent_inventory_manager/data/stores.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "retail_inventory_data" {
  name   = "retail/data/inventory.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/retail/intelligent_inventory_manager/data/inventory.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

# Cyber Incident Response Sub-agent Data
resource "google_storage_bucket_object" "cyber_asset_inventory" {
  name   = "cyber/data/asset_inventory.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/asset_inventory.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "cyber_endpoint_process_events" {
  name   = "cyber/data/endpoint_process_events.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/endpoint_process_events.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "cyber_incident_management" {
  name   = "cyber/data/incident_management.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/incident_management.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "cyber_network_connection_log" {
  name   = "cyber/data/network_connection_log.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/network_connection_log.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "cyber_response_playbooks" {
  name   = "cyber/data/response_playbooks.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/response_playbooks.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "cyber_threat_intelligence_kb" {
  name   = "cyber/data/threat_intelligence_kb.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/threat_intelligence_kb.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "cyber_iam_login_events" {
  name   = "cyber/data/iam_login_events.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/cyber_incident_response/data/iam_login_events.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

# Migration Agent Input File
resource "google_storage_bucket_object" "migration_employees_ddl" {
  name   = "fsi/migration/input/input_employees_ddl.sql"
  source = "${path.module}/../../agent_bar_v2/subagents/fsi/banking_modernization_factory/migration/data/input_employees_ddl.sql"
  bucket = google_storage_bucket.default_data_bucket.name
}

# FinOps Agent Data
resource "google_storage_bucket_object" "finops_csv_data" {
  name   = "finops/data/finops250data.csv"
  source = "${path.module}/../../agent_bar_v2/subagents/cross_industry/cloud_finops_guru/data/finops250data.csv"
  bucket = google_storage_bucket.default_data_bucket.name
}

resource "google_storage_bucket_object" "finops_pdf_data" {
  name   = "finops/data/ACME business document.pdf"
  source = "${path.module}/../../agent_bar_v2/subagents/cross_industry/cloud_finops_guru/data/ACME business document.pdf"
  bucket = google_storage_bucket.default_data_bucket.name
}

# Clinical Handover Sub-agent Data
resource "google_storage_bucket_object" "clinical_handover_patient_data" {
  name   = "clinical_handover/patients/MHID123456789.txt"
  source = "${path.module}/../../agent_bar_v2/subagents/hcls/patient_handover/data/MHID123456789.txt"
  bucket = google_storage_bucket.default_data_bucket.name
}

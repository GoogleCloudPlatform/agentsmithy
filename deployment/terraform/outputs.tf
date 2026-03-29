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

output "project_id" {
  description = "The Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "The region where resources are deployed"
  value       = var.region
}

output "agent_service_account_email" {
  description = "The email of the service account created for the agent"
  value       = google_service_account.agent_sa.email
}

output "artifact_registry_repository_id" {
  description = "The ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.agent_repo.id
}

output "default_data_bucket_name" {
  description = "The name of the GCS default data bucket"
  value       = google_storage_bucket.default_data_bucket.name
}

output "product_ad_generation_bucket_name" {
  description = "The name of the GCS bucket for product ad generation"
  value       = google_storage_bucket.product_ad_generation_bucket.name
}

output "campaign_manager_bucket_name" {
  description = "The name of the GCS bucket for campaign manager"
  value       = google_storage_bucket.campaign_manager_bucket.name
}

output "meeting_intelligence_bucket_name" {
  description = "The name of the GCS bucket for meeting intelligence"
  value       = google_storage_bucket.meeting_intelligence_bucket.name
}

output "macroeconomics_bucket_name" {
  description = "The name of the GCS bucket for macroeconomics"
  value       = google_storage_bucket.macroeconomics_bucket.name
}

# BigQuery Outputs
output "bq_finsights_dataset_id" {
  value = google_bigquery_dataset.finsights_dataset.dataset_id
}

output "bq_cyber_guardian_dataset_id" {
  value = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
}

output "bq_finops_dataset_id" {
  value = google_bigquery_dataset.finops_dataset.dataset_id
}

output "bq_finops_table_id" {
  value = google_bigquery_table.finops_table.table_id
}

output "bq_kg_dataset_id" {
  value = google_bigquery_dataset.kg_dataset.dataset_id
}

output "bq_retail_dataset_id" {
  value = google_bigquery_dataset.retail_dataset.dataset_id
}

output "bq_retail_product_table_id" {
  value = google_bigquery_table.retail_product_table.table_id
}

output "bq_retail_store_table_id" {
  value = google_bigquery_table.retail_store_table.table_id
}

output "bq_retail_inventory_table_id" {
  value = google_bigquery_table.retail_inventory_table.table_id
}

# Discovery Engine Outputs
output "datastore_finops_id" {
  value = google_discovery_engine_data_store.finops_datastore.name
}

output "datastore_retail_id" {
  value = google_discovery_engine_data_store.retail_datastore.data_store_id
}

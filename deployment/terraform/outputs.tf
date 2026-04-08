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

# Project and General
output "GOOGLE_CLOUD_PROJECT" {
  description = "The Google Cloud Project ID"
  value       = var.project_id
}

output "REGION" {
  description = "The region where resources are deployed"
  value       = var.region
}

output "AGENT_SERVICE_ACCOUNT_EMAIL" {
  description = "The email of the service account created for the agent"
  value       = google_service_account.agent_sa.email
}

output "ARTIFACT_REGISTRY_REPOSITORY_ID" {
  description = "The ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.agent_repo.id
}

# Storage Buckets (Formatted with gs:// prefix where app requires it)
output "GCS_BUCKET" {
  description = "The URI of the GCS default data bucket"
  value       = "gs://${google_storage_bucket.default_data_bucket.name}"
}

output "GCS_BUCKET_PRODUCT_AD_GENERATION" {
  description = "The URI of the GCS bucket for product ad generation"
  value       = "gs://${google_storage_bucket.product_ad_generation_bucket.name}"
}

output "GCS_BUCKET_CAMPAING_MANAGER" {
  description = "The name of the GCS bucket for campaign manager"
  value       = google_storage_bucket.campaign_manager_bucket.name
}

output "GCS_BUCKET_MEETING_INTELLIGENCE" {
  description = "The name of the GCS bucket for meeting intelligence"
  value       = google_storage_bucket.meeting_intelligence_bucket.name
}

output "GCS_BUCKET_MACROECONOMICS" {
  description = "The name of the GCS bucket for macroeconomics"
  value       = google_storage_bucket.macroeconomics_bucket.name
}

# BigQuery Datasets & Tables
output "BQ_FINSIGHTS_DATASET_ID" {
  value = google_bigquery_dataset.finsights_dataset.dataset_id
}

output "BQ_CYBER_GUARDIAN_DATASET_ID" {
  value = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
}

output "BQ_FINOPS_DATASET_ID" {
  value = google_bigquery_dataset.finops_dataset.dataset_id
}

output "BQ_FINOPS_TABLE_ID" {
  value = google_bigquery_table.finops_table.table_id
}

output "BQ_KG_DATASET_ID" {
  value = google_bigquery_dataset.kg_dataset.dataset_id
}

output "BQ_RETAIL_DATASET_ID" {
  value = google_bigquery_dataset.retail_dataset.dataset_id
}

output "BQ_RETAIL_PRODUCT_TABLE_ID" {
  value = google_bigquery_table.retail_product_table.table_id
}

output "BQ_RETAIL_STORE_TABLE_ID" {
  value = google_bigquery_table.retail_store_table.table_id
}

output "BQ_RETAIL_INVENTORY_TABLE_ID" {
  value = google_bigquery_table.retail_inventory_table.table_id
}

# Discovery Engine Outputs
output "DATASTORE_FINOPS_ID" {
  value = google_discovery_engine_data_store.finops_datastore.name
}

output "DATASTORE_RETAIL_ID" {
  value = google_discovery_engine_data_store.retail_datastore.data_store_id
}
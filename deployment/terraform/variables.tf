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

variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The default region for resources"
  type        = string
  default     = "us-central1"
}

variable "sa_account_id" {
  description = "Service account ID for the agent"
  type        = string
  default     = "agent-bar-v2-sa"
}

variable "sa_display_name" {
  description = "Service account display name for the agent"
  type        = string
  default     = "Agent Bar v2 Service Account"
}

variable "ar_repository_id" {
  description = "Artifact Registry repository ID"
  type        = string
  default     = "agent-bar-v2-repo"
}

variable "ar_description" {
  description = "Artifact Registry repository description"
  type        = string
  default     = "Docker repository for Agent Bar v2 images"
}

variable "bucket_suffix_default_data" {
  description = "Suffix for the default data bucket"
  type        = string
  default     = "-default-data"
}

variable "bucket_suffix_product_ad_generation" {
  description = "Suffix for the product ad generation bucket"
  type        = string
  default     = "-cross-pag"
}

variable "bucket_suffix_campaign_manager" {
  description = "Suffix for the campaign manager bucket"
  type        = string
  default     = "-cross-gcma"
}

variable "bucket_suffix_meeting_intelligence" {
  description = "Suffix for the meeting intelligence bucket"
  type        = string
  default     = "-cross-mi"
}

# BigQuery Variables
variable "bq_finops_dataset_id" {
  description = "BigQuery dataset ID for FinOps"
  type        = string
  default     = "finops"
}

variable "bq_finops_table_id" {
  description = "BigQuery table ID for FinOps"
  type        = string
  default     = "finops10ktable"
}

variable "bq_kg_dataset_id" {
  description = "BigQuery dataset ID for Knowledge Graph"
  type        = string
  default     = "kg_agent"
}

variable "bq_retail_dataset_id" {
  description = "BigQuery dataset ID for Retail"
  type        = string
  default     = "retail"
}

variable "bq_retail_product_table_id" {
  description = "BigQuery table ID for Retail products"
  type        = string
  default     = "products"
}

variable "bq_retail_store_table_id" {
  description = "BigQuery table ID for Retail stores"
  type        = string
  default     = "store"
}

variable "bq_retail_inventory_table_id" {
  description = "BigQuery table ID for Retail inventory"
  type        = string
  default     = "inventory"
}

# Spanner Variables
variable "spanner_kg_instance" {
  description = "Spanner instance name for Knowledge Graph"
  type        = string
  default     = "kg_instance"
}

variable "spanner_kg_database" {
  description = "Spanner database name for Knowledge Graph"
  type        = string
  default     = "gk_database"
}

# Discovery Engine / Vertex AI Search Variables
variable "datastore_finops_id" {
  description = "Discovery Engine Data Store ID for FinOps"
  type        = string
  default     = "finops"
}

variable "datastore_retail_id" {
  description = "Discovery Engine Data Store ID for Retail Customer Support"
  type        = string
  default     = "retail"
}

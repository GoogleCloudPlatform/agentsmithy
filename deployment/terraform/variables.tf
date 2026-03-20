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
}

variable "sa_display_name" {
  description = "Service account display name for the agent"
  type        = string
}

variable "ar_repository_id" {
  description = "Artifact Registry repository ID"
  type        = string
}

variable "ar_description" {
  description = "Artifact Registry repository description"
  type        = string
}

variable "bucket_suffix_default_data" {
  description = "Suffix for the default data bucket"
  type        = string
}

variable "bucket_suffix_product_ad_generation" {
  description = "Suffix for the product ad generation bucket"
  type        = string
}

variable "bucket_suffix_campaign_manager" {
  description = "Suffix for the campaign manager bucket"
  type        = string
}

variable "bucket_suffix_meeting_intelligence" {
  description = "Suffix for the meeting intelligence bucket"
  type        = string
}

# BigQuery Variables
variable "bq_finops_dataset_id" {
  description = "BigQuery dataset ID for FinOps"
  type        = string
}

variable "bq_finops_table_id" {
  description = "BigQuery table ID for FinOps"
  type        = string
}

variable "bq_kg_dataset_id" {
  description = "BigQuery dataset ID for Knowledge Graph"
  type        = string
}

variable "bq_retail_dataset_id" {
  description = "BigQuery dataset ID for Retail"
  type        = string
}

variable "bq_retail_product_table_id" {
  description = "BigQuery table ID for Retail products"
  type        = string
}

variable "bq_retail_store_table_id" {
  description = "BigQuery table ID for Retail stores"
  type        = string
}

variable "bq_retail_inventory_table_id" {
  description = "BigQuery table ID for Retail inventory"
  type        = string
}

# Spanner Variables
variable "spanner_kg_instance" {
  description = "Spanner instance name for Knowledge Graph"
  type        = string
}

variable "spanner_kg_database" {
  description = "Spanner database name for Knowledge Graph"
  type        = string
}

# Discovery Engine / Vertex AI Search Variables
variable "datastore_finops_id" {
  description = "Discovery Engine Data Store ID for FinOps"
  type        = string
}

variable "datastore_retail_id" {
  description = "Discovery Engine Data Store ID for Retail Customer Support"
  type        = string
}

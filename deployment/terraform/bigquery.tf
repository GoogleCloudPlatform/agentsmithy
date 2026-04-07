# FinOps BigQuery Dataset & Table
resource "google_bigquery_dataset" "finops_dataset" {
  dataset_id = var.bq_finops_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [time_sleep.wait_for_api_enablement]
}

resource "google_bigquery_table" "finops_table" {
  dataset_id          = google_bigquery_dataset.finops_dataset.dataset_id
  table_id            = var.bq_finops_table_id
  project             = var.project_id
  deletion_protection = false
}

# Knowledge Graph BigQuery Dataset
resource "google_bigquery_dataset" "kg_dataset" {
  dataset_id = var.bq_kg_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [time_sleep.wait_for_api_enablement]
}

# Retail Inventory BigQuery Dataset & Tables
resource "google_bigquery_dataset" "retail_dataset" {
  dataset_id = var.bq_retail_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [time_sleep.wait_for_api_enablement]
}

# Finsights BigQuery Dataset
resource "google_bigquery_dataset" "finsights_dataset" {
  dataset_id = var.bq_finsights_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [time_sleep.wait_for_api_enablement]
}

# Cyber Guardian BigQuery Dataset
resource "google_bigquery_dataset" "cyber_guardian_dataset" {
  dataset_id = var.bq_cyber_guardian_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [time_sleep.wait_for_api_enablement]
}

resource "google_bigquery_table" "retail_product_table" {
  dataset_id          = google_bigquery_dataset.retail_dataset.dataset_id
  table_id            = var.bq_retail_product_table_id
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "retail_store_table" {
  dataset_id          = google_bigquery_dataset.retail_dataset.dataset_id
  table_id            = var.bq_retail_store_table_id
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "retail_inventory_table" {
  dataset_id          = google_bigquery_dataset.retail_dataset.dataset_id
  table_id            = var.bq_retail_inventory_table_id
  project             = var.project_id
  deletion_protection = false
}

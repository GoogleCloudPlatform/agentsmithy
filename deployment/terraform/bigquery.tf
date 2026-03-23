# FinOps BigQuery Dataset & Table
resource "google_bigquery_dataset" "finops_dataset" {
  dataset_id = var.bq_finops_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [google_project_service.enabled_apis]
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
  depends_on = [google_project_service.enabled_apis]
}

# Retail Inventory BigQuery Dataset & Tables
resource "google_bigquery_dataset" "retail_dataset" {
  dataset_id = var.bq_retail_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [google_project_service.enabled_apis]
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

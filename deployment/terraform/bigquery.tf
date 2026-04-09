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

# Retail Inventory BigQuery Dataset & Tables
resource "google_bigquery_dataset" "retail_dataset" {
  dataset_id = var.bq_retail_dataset_id
  location   = var.region
  project    = var.project_id
  depends_on = [time_sleep.wait_for_api_enablement]
}

# Financial Insights BigQuery Dataset
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

resource "google_bigquery_table" "retail_product_staging" {
  dataset_id          = google_bigquery_dataset.retail_dataset.dataset_id
  table_id            = "products_staging"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_job" "load_products_staging" {
  project = var.project_id

  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.retail_products_data.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.retail_dataset.dataset_id
      table_id   = google_bigquery_table.retail_product_staging.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_retail_stores" {
  project = var.project_id

  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.retail_stores_data.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.retail_dataset.dataset_id
      table_id   = google_bigquery_table.retail_store_table.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_retail_inventory" {
  project = var.project_id

  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.retail_inventory_data.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.retail_dataset.dataset_id
      table_id   = google_bigquery_table.retail_inventory_table.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "create_model_and_embeddings" {
  project = var.project_id

  query {
    query = <<EOF
      CREATE OR REPLACE MODEL `${var.project_id}.${google_bigquery_dataset.retail_dataset.dataset_id}.text_embedding`
      OPTIONS(
        model_type='text_embedding_004',
        endpoint='text-embedding-004'
      ) AS
      SELECT product_name AS content
      FROM `${var.project_id}.${google_bigquery_dataset.retail_dataset.dataset_id}.${google_bigquery_table.retail_product_staging.table_id}`;

      CREATE OR REPLACE TABLE `${var.project_id}.${google_bigquery_dataset.retail_dataset.dataset_id}.${google_bigquery_table.retail_product_table.table_id}` AS
      SELECT *, ml_generate_embedding_result AS text_embedding
      FROM ML.GENERATE_EMBEDDING(
        MODEL `${var.project_id}.${google_bigquery_dataset.retail_dataset.dataset_id}.text_embedding`,
        (SELECT * FROM `${var.project_id}.${google_bigquery_dataset.retail_dataset.dataset_id}.${google_bigquery_table.retail_product_staging.table_id}`)
      );
    EOF
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_job.load_products_staging,
    google_bigquery_table.retail_product_table
  ]
}

# Cyber Incident Response Tables
resource "google_bigquery_table" "cyber_asset_inventory" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "asset_inventory"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "cyber_endpoint_process_events" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "endpoint_process_events"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "cyber_incident_management" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "incident_management"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "cyber_network_connection_log" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "network_connection_log"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "cyber_response_playbooks" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "response_playbooks"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "cyber_threat_intelligence_kb" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "threat_intelligence_kb"
  project             = var.project_id
  deletion_protection = false
}

resource "google_bigquery_table" "cyber_iam_login_events" {
  dataset_id          = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
  table_id            = "iam_login_events"
  project             = var.project_id
  deletion_protection = false
}

# Load Jobs for Cyber Incident Response
resource "google_bigquery_job" "load_cyber_asset_inventory" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_asset_inventory.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_asset_inventory.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_cyber_endpoint_process_events" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_endpoint_process_events.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_endpoint_process_events.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_cyber_incident_management" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_incident_management.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_incident_management.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_cyber_network_connection_log" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_network_connection_log.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_network_connection_log.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_cyber_response_playbooks" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_response_playbooks.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_response_playbooks.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_cyber_threat_intelligence_kb" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_threat_intelligence_kb.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_threat_intelligence_kb.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

resource "google_bigquery_job" "load_cyber_iam_login_events" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.cyber_iam_login_events.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.cyber_guardian_dataset.dataset_id
      table_id   = google_bigquery_table.cyber_iam_login_events.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

# Load Job for FinOps Data
resource "google_bigquery_job" "load_finops_data" {
  project = var.project_id
  load {
    source_uris = ["gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.finops_csv_data.name}"]
    destination_table {
      project_id = var.project_id
      dataset_id = google_bigquery_dataset.finops_dataset.dataset_id
      table_id   = google_bigquery_table.finops_table.table_id
    }
    write_disposition = "WRITE_TRUNCATE"
    autodetect        = true
    source_format     = "CSV"
    skip_leading_rows = 1
  }
}

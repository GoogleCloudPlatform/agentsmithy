resource "google_discovery_engine_data_store" "finops_datastore" {
  location          = "global"
  data_store_id     = var.datastore_finops_id
  display_name      = "Finops Data Store"
  industry_vertical = "GENERIC"
  content_config    = "NO_CONTENT"
  project           = var.project_id
  depends_on        = [time_sleep.wait_for_api_enablement]
}

resource "google_discovery_engine_data_store" "retail_datastore" {
  location          = "global"
  data_store_id     = var.datastore_retail_id
  display_name      = "Retail Support Data Store"
  industry_vertical = "GENERIC"
  content_config    = "NO_CONTENT"
  project           = var.project_id
  depends_on        = [time_sleep.wait_for_api_enablement]
}

resource "null_resource" "ingest_retail_data" {
  triggers = {
    datastore_id = google_discovery_engine_data_store.retail_datastore.data_store_id
  }

  provisioner "local-exec" {
    command = "gcloud discoveryengine data-stores documents import ${google_discovery_engine_data_store.retail_datastore.data_store_id} --location=global --gcs-uri=gs://cloud-samples-data/dialogflow-cx/google-store/*.html --project=${var.project_id}"
  }

  depends_on = [google_discovery_engine_data_store.retail_datastore]
}

resource "null_resource" "ingest_finops_data" {
  triggers = {
    datastore_id = google_discovery_engine_data_store.finops_datastore.data_store_id
  }

  provisioner "local-exec" {
    command = "gcloud discoveryengine data-stores documents import ${google_discovery_engine_data_store.finops_datastore.data_store_id} --location=global --gcs-uri=gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.finops_pdf_data.name} --project=${var.project_id}"
  }

  depends_on = [google_discovery_engine_data_store.finops_datastore, google_storage_bucket_object.finops_pdf_data]
}

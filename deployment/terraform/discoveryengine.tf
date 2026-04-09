resource "google_discovery_engine_data_store" "finops_datastore" {
  location          = "global"
  data_store_id     = var.datastore_finops_id
  display_name      = "Finops Data Store"
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED"
  project           = var.project_id
  depends_on        = [time_sleep.wait_for_api_enablement]
}

resource "google_discovery_engine_data_store" "retail_datastore" {
  location          = "global"
  data_store_id     = var.datastore_retail_id
  display_name      = "Retail Support Data Store"
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED"
  project           = var.project_id
  depends_on        = [time_sleep.wait_for_api_enablement]
}

resource "null_resource" "ingest_retail_data" {
  triggers = {
    datastore_id = google_discovery_engine_data_store.retail_datastore.data_store_id
  }

  provisioner "local-exec" {
    command = <<EOT
# Clear previous file if any
> retail.jsonl

counter=0
gsutil ls gs://cloud-samples-data/dialogflow-cx/google-store/*.html | while read -r uri; do
  echo "{\"id\": \"doc-$counter\", \"jsonData\": \"{}\", \"content\": {\"mimeType\": \"text/html\", \"uri\": \"$uri\"}}" >> retail.jsonl
  counter=$((counter+1))
done

gsutil cp retail.jsonl gs://${google_storage_bucket.default_data_bucket.name}/retail.jsonl

curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
"https://discoveryengine.googleapis.com/v1/projects/${var.project_id}/locations/global/collections/default_collection/dataStores/${google_discovery_engine_data_store.retail_datastore.data_store_id}/branches/default_branch/documents:import" \
-d '{
  "gcsSource": {
    "inputUris": ["gs://${google_storage_bucket.default_data_bucket.name}/retail.jsonl"]
  }
}'
EOT
  }

  depends_on = [google_discovery_engine_data_store.retail_datastore]
}

resource "null_resource" "ingest_finops_data" {
  triggers = {
    datastore_id = google_discovery_engine_data_store.finops_datastore.data_store_id
  }

  provisioner "local-exec" {
    command = <<EOT
echo "{\"id\": \"doc-0\", \"jsonData\": \"{}\", \"content\": {\"mimeType\": \"application/pdf\", \"uri\": \"gs://${google_storage_bucket.default_data_bucket.name}/${google_storage_bucket_object.finops_pdf_data.name}\"}}" > finops.jsonl

gsutil cp finops.jsonl gs://${google_storage_bucket.default_data_bucket.name}/finops.jsonl

curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
"https://discoveryengine.googleapis.com/v1/projects/${var.project_id}/locations/global/collections/default_collection/dataStores/${google_discovery_engine_data_store.finops_datastore.data_store_id}/branches/default_branch/documents:import" \
-d '{
  "gcsSource": {
    "inputUris": ["gs://${google_storage_bucket.default_data_bucket.name}/finops.jsonl"]
  }
}'
EOT
  }

  depends_on = [google_discovery_engine_data_store.finops_datastore, google_storage_bucket_object.finops_pdf_data]
}

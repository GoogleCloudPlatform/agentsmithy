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

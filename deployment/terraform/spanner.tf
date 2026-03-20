resource "google_spanner_instance" "kg_instance" {
  config           = "regional-${var.region}"
  display_name     = "Knowledge Graph Instance"
  name             = var.spanner_kg_instance
  project          = var.project_id
  processing_units = 100
  depends_on       = [google_project_service.enabled_apis]
}

resource "google_spanner_database" "kg_database" {
  instance            = google_spanner_instance.kg_instance.name
  name                = var.spanner_kg_database
  project             = var.project_id
  deletion_protection = false
}

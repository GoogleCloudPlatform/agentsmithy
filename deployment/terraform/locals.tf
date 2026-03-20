locals {
  services = [
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com",
    "speech.googleapis.com",
    "run.googleapis.com", # Required for Cloud Run deployment
    "bigquery.googleapis.com",
    "spanner.googleapis.com",
    "discoveryengine.googleapis.com"
  ]

  agent_roles = [
    "roles/aiplatform.user",
    "roles/aiplatform.admin",
    "roles/storage.objectUser",
    "roles/logging.logWriter",
    "roles/artifactregistry.reader",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/spanner.databaseAdmin",
    "roles/spanner.databaseReader",
    "roles/discoveryengine.editor",
  ]
}

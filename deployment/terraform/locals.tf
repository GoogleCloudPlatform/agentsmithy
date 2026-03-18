locals {
  services = [
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com",
    "speech.googleapis.com",
    "run.googleapis.com" # Required for Cloud Run deployment
  ]

  agent_roles = [
    "roles/aiplatform.user",
    "roles/storage.objectUser",
    "roles/logging.logWriter",
    "roles/artifactregistry.reader",
  ]
}

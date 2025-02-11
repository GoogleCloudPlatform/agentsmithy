locals {
  cicd_services = [
    "cloudbuild.googleapis.com",
    "discoveryengine.googleapis.com",
    "aiplatform.googleapis.com",
    "serviceusage.googleapis.com",
    "bigquery.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudtrace.googleapis.com"
  ]

  shared_services = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "discoveryengine.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "bigquery.googleapis.com",
    "serviceusage.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com"
  ]

  deploy_project_ids = {
    prod    = var.prod_project_id
  }

  # Derived variables based on agent name
  telemetry_bigquery_dataset_id = "telemetry_${lower(replace(var.agent_name, " ", "_"))}_sink"
  telemetry_sink_name = "telemetry_logs_${lower(replace(var.agent_name, " ", "_"))}"
  telemetry_logs_filter = "jsonPayload.attributes.\"traceloop.association.properties.log_type\"=\"tracing\" jsonPayload.resource.attributes.\"service.name\"=\"${var.agent_name}\""

  feedback_bigquery_dataset_id = "feedback_${lower(replace(var.agent_name, " ", "_"))}_sink"
  feedback_sink_name = "feedback_logs_${lower(replace(var.agent_name, " ", "_"))}"
  feedback_logs_filter = "jsonPayload.log_type=\"feedback\""

  cicd_runner_sa_name = "${lower(replace(var.agent_name, " ", "-"))}-runner"
  cloud_run_app_sa_name = "${lower(replace(var.agent_name, " ", "-"))}-cr-sa"

  suffix_bucket_name_load_test_results = "${lower(replace(var.agent_name, " ", "-"))}-cicd-load-test-results"
  artifact_registry_repo_name = "${lower(replace(var.agent_name, " ", "-"))}-repository"
}


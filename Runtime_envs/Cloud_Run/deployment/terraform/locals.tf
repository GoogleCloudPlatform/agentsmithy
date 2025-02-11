# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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


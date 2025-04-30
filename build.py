# Copyright 2025 Google LLC. All Rights Reserved.
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
# pylint: disable=C0301, R1714, R0917, W0719, W0718, W0621, W1510
"""Builds and deploys a custom agent based on the user configuration

The account running this script should have the following recommended roles:
- roles/serviceusage.serviceUsageAdmin
- roles/resourcemanager.projectIamAdmin
- roles/iam.serviceAccountAdmin
- roles/iam.serviceAccountUser
- roles/storage.admin
- roles/artifactregistry.admin
- roles/run.admin
- roles/cloudbuild.builds.editor
"""
import os
import re
import subprocess
import sys
from uuid import uuid4

# TODO: Install  pip install poetry and run poetry install
from google.cloud import discoveryengine
from google.api_core.client_options import ClientOptions
import vertexai
import yaml



def read_yaml_file(filepath: str) -> dict:
    """Reads a yaml and returns file contents as a dict. Defaults to utf-8 encoding.

    Args:
        filepath (str): Path to the yaml.

    Returns:
        dict: Contents of the yaml.

    Raises:
        Exception: If an error is encountered reading the file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            file_dict = yaml.safe_load(file)
        file.close()
    except yaml.YAMLError as err:
        raise yaml.YAMLError(f"Error reading file. {err}") from err
    return file_dict


ENV_TAG = "dev"
DEPLOY_TO_AGENT_ENGINE = False

# Cloud Run services config.
BACKEND_PATH = "Runtime_env"
BACKEND_CONFIG_FILE = f"{BACKEND_PATH}/deployment/config/{ENV_TAG}.yaml"
BACKEND_BUILD_FILE = f"{BACKEND_PATH}/deployment/cd/{ENV_TAG}.yaml"
FRONTEND_PATH = "ChatbotUI"
FRONTEND_CONFIG_FILE = f"{FRONTEND_PATH}/src/environments/environment.ts"
FRONTEND_BUILD_FILE = f"{FRONTEND_PATH}/deployment/cd/{ENV_TAG}.yaml"

backend_yaml_config = read_yaml_file(BACKEND_CONFIG_FILE)

# Check that keys exist
required_keys = [
    "PROJECT_ID", "VERTEX_AI_LOCATION", "AGENT_FOUNDATION_MODEL",
    "AGENT_INDUSTRY_TYPE", "AGENT_ORCHESTRATION_FRAMEWORK", "USER_AGENT",
    "AGENT_DESCRIPTION", "AGENT_BUILDER_LOCATION"
]
if not all(key in backend_yaml_config for key in required_keys):
    raise KeyError(f"Missing Required keys in {BACKEND_CONFIG_FILE}. Required Keys: {required_keys}")

# Grab env vars previously set by user
PROJECT_ID = backend_yaml_config["PROJECT_ID"]
REGION = backend_yaml_config["VERTEX_AI_LOCATION"]
AGENT_FOUNDATION_MODEL = backend_yaml_config["AGENT_FOUNDATION_MODEL"]
AGENT_INDUSTRY_TYPE = backend_yaml_config["AGENT_INDUSTRY_TYPE"]
AGENT_ORCHESTRATION_FRAMEWORK = backend_yaml_config["AGENT_ORCHESTRATION_FRAMEWORK"]
AGENT_NAME = backend_yaml_config["USER_AGENT"]
AGENT_DESCRIPTION = backend_yaml_config["AGENT_DESCRIPTION"]
DATA_STORE_LOCATION = backend_yaml_config["AGENT_BUILDER_LOCATION"]

# Terraform Constants.
TERRAFORM_DIRECTORY = f"{BACKEND_PATH}/deployment/terraform"
TERRAFORM_VAR_FILE = "vars/env.tfvars"

# GCP resources constants.
ARTIFACT_REGISTRY_REPOSITORY = f"{PROJECT_ID.lower().replace(' ', '-')}-{AGENT_NAME.lower().replace(' ', '-')}-repository"

CLOUD_RUN_BACKEND_SERVICE_NAME = AGENT_NAME.lower().replace(" ", "-") + "-backend"
CLOUD_RUN_FRONTEND_SERVICE_NAME = AGENT_NAME.lower().replace(" ", "-") + "-frontend"

DATASTORE_INDUSTRY_SOURCES_MAP = {
    "finance": "gs://cloud-samples-data/gen-app-builder/search/alphabet-investor-pdfs/*.pdf",
    "healthcare": "gs://cloud-samples-data/vertex-ai/medlm/primock57/transcripts/*.txt",
    "retail": "gs://cloud-samples-data/dialogflow-cx/google-store/*.html",
}
DATA_STORE_ID = f"agent_smithy_data_store_{uuid4()}"
DATA_STORE_NAME = f"{PROJECT_ID.lower().replace(' ', '-')}-{AGENT_NAME.lower().replace(' ', '-')}-datastore"
SEARCH_APP_ENGINE_ID = f"agent_smithy_search_engine_{uuid4()}"
GCS_STAGING_BUCKET = f"gs://{PROJECT_ID.lower().replace(' ', '-')}-agents-staging"


vertexai.init(
    project=PROJECT_ID,
    location=REGION,
    staging_bucket=GCS_STAGING_BUCKET
)

def deploy_terraform_infrastructure(directory: str, variables_file: str):
    init_terraform_command = ["terraform", f"-chdir={directory}", "init"]
    apply_terraform_command = ["terraform", f"-chdir={directory}", "apply", "--var-file", variables_file]

    search_and_replace_file(f"{directory}/{variables_file}", r"project_id = \"(.*?)\"", f'project_id = "{PROJECT_ID}"')
    search_and_replace_file(f"{directory}/{variables_file}", r"region = \"(.*?)\"", f'region = "{REGION}"')
    search_and_replace_file(f"{directory}/{variables_file}", r"agent_name = \"(.*?)\"", f'agent_name = "{AGENT_NAME}"')
    search_and_replace_file(f"{directory}/{variables_file}", r"vertex_ai_staging_bucket = \"(.*?)\"", f'vertex_ai_staging_bucket = "{GCS_STAGING_BUCKET.split("/")[2]}"')
    search_and_replace_file(f"{directory}/{variables_file}", r"artifact_registry_repo_name = \"(.*?)\"", f'artifact_registry_repo_name = "{ARTIFACT_REGISTRY_REPOSITORY}"')
    search_and_replace_file(f"{directory}/{variables_file}", r"backend_cloud_run_service_name = \"(.*?)\"", f'backend_cloud_run_service_name = "{CLOUD_RUN_BACKEND_SERVICE_NAME}"')
    search_and_replace_file(f"{directory}/{variables_file}", r"frontend_cloud_run_service_name = \"(.*?)\"", f'frontend_cloud_run_service_name = "{CLOUD_RUN_FRONTEND_SERVICE_NAME}"')

    subprocess.run(init_terraform_command, check=True)
    subprocess.run(apply_terraform_command, check=True)

def create_data_store() -> str:
    client_options = (
        ClientOptions(api_endpoint=f"{DATA_STORE_LOCATION}-discoveryengine.googleapis.com")
        if DATA_STORE_LOCATION != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)
    parent = client.collection_path(
        project=PROJECT_ID,
        location=DATA_STORE_LOCATION,
        collection="default_collection",
    )
    data_store = discoveryengine.DataStore(
        display_name=DATA_STORE_NAME,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=DATA_STORE_ID,
        data_store=data_store,
    )
    operation = client.create_data_store(request=request)
    print(f"Waiting for operation to complete: {operation.operation.name}")
    operation.result()

def populate_data_store(industry: str):
    client_options = (
        ClientOptions(api_endpoint=f"{DATA_STORE_LOCATION}-discoveryengine.googleapis.com")
        if DATA_STORE_LOCATION != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DocumentServiceClient(client_options=client_options)
    parent = client.branch_path(
        project=PROJECT_ID,
        location=DATA_STORE_LOCATION,
        data_store=DATA_STORE_ID,
        branch="default_branch",
    )
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[DATASTORE_INDUSTRY_SOURCES_MAP[industry]],
            data_schema="content",
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )
    operation = client.import_documents(request=request)
    print(f"Import operation will keep on running on the background: {operation.operation.name}")

def create_search_app() -> str:
    client_options = (
        ClientOptions(api_endpoint=f"{DATA_STORE_LOCATION}-discoveryengine.googleapis.com")
        if DATA_STORE_LOCATION != "global"
        else None
    )

    # Create a client
    client = discoveryengine.EngineServiceClient(client_options=client_options)

    # The full resource name of the collection
    # e.g. projects/{project}/locations/{location}/collections/default_collection
    parent = client.collection_path(
        project=PROJECT_ID,
        location=DATA_STORE_LOCATION,
        collection="default_collection",
    )

    engine = discoveryengine.Engine(
        display_name=SEARCH_APP_ENGINE_ID,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_type=discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
        search_engine_config=discoveryengine.Engine.SearchEngineConfig(
            search_tier=discoveryengine.SearchTier.SEARCH_TIER_ENTERPRISE,
            search_add_ons=[discoveryengine.SearchAddOn.SEARCH_ADD_ON_LLM],
        ),
        data_store_ids=[DATA_STORE_ID],
    )

    request = discoveryengine.CreateEngineRequest(
        parent=parent,
        engine=engine,
        engine_id=SEARCH_APP_ENGINE_ID,
    )
    operation = client.create_engine(request=request)
    print(f"Waiting for operation to complete: {operation.operation.name}")
    operation.result()

def run_agent_engine_deployment() -> str:
    # TODO figure out a better way to dynamically get these env after they are written
    navigate_to_directory(BACKEND_PATH)
    sys.path.insert(0, os.getcwd())

    from app.orchestration.server_utils import get_agent_from_config
    from app.utils.utils import deploy_agent_to_agent_engine


    agent_manager = get_agent_from_config(
        agent_orchestration_framework=AGENT_ORCHESTRATION_FRAMEWORK,
        agent_foundation_model=AGENT_FOUNDATION_MODEL,
        industry_type=AGENT_INDUSTRY_TYPE
    )

    remote_agent = None
    if AGENT_ORCHESTRATION_FRAMEWORK == "llamaindex_agent":
        remote_agent = deploy_agent_to_agent_engine(
            agent_manager,
            AGENT_NAME,
            AGENT_DESCRIPTION
        )

    elif AGENT_ORCHESTRATION_FRAMEWORK == "langgraph_vertex_ai_agent_engine_agent" or AGENT_ORCHESTRATION_FRAMEWORK == "langchain_vertex_ai_agent_engine_agent":
        remote_agent = deploy_agent_to_agent_engine(
            agent_manager.agent_executor,
            AGENT_NAME,
            AGENT_DESCRIPTION
        )
    elif AGENT_ORCHESTRATION_FRAMEWORK == "vertex_ai_agent_framework_agent":
        remote_agent = deploy_agent_to_agent_engine(
            agent_manager.agent_executor.agent,
            AGENT_NAME,
            AGENT_DESCRIPTION
        )

    if not remote_agent.resource_name:
        raise Exception("Error deploying Agent to Agent Engine.")

    try:
        # If AGENT_ENGINE_RESOURCE_ID is set, then the agent will query the remote agent
        with open(BACKEND_CONFIG_FILE.replace(f"{BACKEND_PATH}/", ""), "a", encoding="utf-8") as f:
            f.write(f"\nAGENT_ENGINE_RESOURCE_ID: {remote_agent.resource_name}\n")
        f.close()
    except FileNotFoundError:
        print(f"`{BACKEND_CONFIG_FILE.replace(f'{BACKEND_PATH}/', '')}` file not found.")

    navigate_to_directory(".")

    # Retrieve the project number associated with your project ID
    project_number = subprocess.run(
        ["gcloud", "projects", "describe", PROJECT_ID, "--format=value(projectNumber)"],
        check=True,
        capture_output=True,
        text=True
    ).stdout.strip()

    # Add Discovery Engine Editor to the Agent Engine Service account
    iam_command = [
        "gcloud",
        "projects",
        "add-iam-policy-binding",
        PROJECT_ID,
        f"--member=serviceAccount:service-{project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com",
        "--role=roles/discoveryengine.editor",
        "--no-user-output-enabled"
    ]
    subprocess.run(iam_command, check=True)

    return remote_agent.resource_name


def get_cloud_run_url(region: str, service_name: str) -> str:
    try:
        describe = subprocess.run(["gcloud", "run", "services", "describe", service_name, "--region", region], capture_output=True, text=True)
        if describe.returncode == 0:
            url_match = re.search(r"\s+URL:\s+(.*?)\n", describe.stdout)

            if url_match:
                url = url_match.group(1)
                return url
            else:
                print("URL not found in the output.")
                return ""
        else:
            print("Cloud run service does not exist.")
            print("Error describing service (non-zero exit code):")
            print(f"Stdout: {describe.stdout}")
            print(f"Stderr: {describe.stderr}")
            return ""
    except Exception as e:  # Catch any other potential errors
        print(f"An unexpected error occurred: {e}")
        return ""

def configure_backend(gcs_bucket: str, datastore_id: str, frontend_url: str, config_file: str):
    search_and_replace_file(config_file, r"GCS_STAGING_BUCKET:\s(.*?)*\n", f"GCS_STAGING_BUCKET: {gcs_bucket}\n")
    search_and_replace_file(config_file, r"DATA_STORE_ID:\s(.*?)*\n", f"DATA_STORE_ID: {datastore_id}\n")
    search_and_replace_file(config_file, r"FRONTEND_URL:\s(.*?)*\n", f"FRONTEND_URL: {frontend_url}\n")

def configure_frontend(agent_name: str, backend_url: str, env_tag: str, config_file: str):
    search_and_replace_file(config_file, r"const env: string = \"(.*?)\"", f'const env: string = "{env_tag}"')
    search_and_replace_file(config_file, r"backendURL = \"(.*?)\"", f'backendURL = "{backend_url}/"')
    search_and_replace_file(config_file, r"chatbotName = \"(.*?)\"", f'chatbotName = "{agent_name}"')

def build_and_deploy_cloud_run(
        project_id: str,
        region: str,
        container_name: str,
        artifact_registry_name: str,
        service_name: str,
        build_file_location: str,
        is_backend: bool,
    ):
    push_command = [
        "gcloud",
        "builds",
        "submit",
        "--config",
        build_file_location,
        "--substitutions",
        f"_PROJECT_ID={project_id},_REGION={region},_CONTAINER_NAME={container_name},_ARTIFACT_REGISTRY_REPO_NAME={artifact_registry_name},_SERVICE_NAME={service_name}",
        BACKEND_PATH if is_backend else FRONTEND_PATH
    ]
    subprocess.run(push_command, check=True)

def navigate_to_directory(directory: str):
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + f"/{directory}")

def search_and_replace_file(file_path: str, search_pattern: str, new_line: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            updated_content = re.sub(search_pattern, new_line, file_content)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        f.close()
    except FileNotFoundError:
        print(f"`{file_path}` file not found.")

if __name__ == "__main__":
    # TODO: Set arguments for calling the script
    #if len(sys.argv) < 2:
    #    print("Usage: python3 local_deploy.py action (e.g action = (clone, run, redeploy))")
    #    exit(1)

    deploy_terraform_infrastructure(TERRAFORM_DIRECTORY, TERRAFORM_VAR_FILE)

    create_data_store()
    populate_data_store(AGENT_INDUSTRY_TYPE)
    create_search_app()

    # Build and deploy BE Service.
    frontend_url = get_cloud_run_url(REGION, CLOUD_RUN_FRONTEND_SERVICE_NAME)
    configure_backend(
        GCS_STAGING_BUCKET,
        DATA_STORE_ID,
        frontend_url,
        BACKEND_CONFIG_FILE
    )

    if DEPLOY_TO_AGENT_ENGINE:
        run_agent_engine_deployment()

    build_and_deploy_cloud_run(
        PROJECT_ID,
        REGION,
        "agent_runtime",
        ARTIFACT_REGISTRY_REPOSITORY,
        CLOUD_RUN_BACKEND_SERVICE_NAME,
        BACKEND_BUILD_FILE,
        True
    )

    # Build and deploy FE Service.
    backend_url = get_cloud_run_url(REGION, CLOUD_RUN_BACKEND_SERVICE_NAME)
    configure_frontend(AGENT_NAME, backend_url, ENV_TAG, FRONTEND_CONFIG_FILE)
    build_and_deploy_cloud_run(
        PROJECT_ID,
        REGION,
        "chatbot_ui",
        ARTIFACT_REGISTRY_REPOSITORY,
        CLOUD_RUN_FRONTEND_SERVICE_NAME,
        FRONTEND_BUILD_FILE,
        False
    )

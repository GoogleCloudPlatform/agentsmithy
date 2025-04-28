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
# pylint: disable=C0301, R1714, R0917, W0719, W0718, W0621, W1510, C0103
import os
import re
import subprocess
import sys
from uuid import uuid4

# Deferred Imports (will be imported once the packages are installed)
discoveryengine = None
ClientOptions = None
vertexai = None

# Note: The account running this script must have Cloud Run Admin (among other things)
# Note: Recommend running this script from inside a venv

# These vars must be set
ENV_TAG = "dev"

# Grab vars previously set by user
AGENT_FOUNDATION_MODEL = "{{AGENT_FOUNDATION_MODEL}}"
AGENT_INDUSTRY_TYPE = "{{AGENT_INDUSTRY_TYPE}}"
AGENT_ORCHESTRATION_FRAMEWORK = "{{AGENT_ORCHESTRATION_FRAMEWORK}}"
AGENT_NAME = "{{AGENT_NAME}}"
AGENT_DESCRIPTION = "{{AGENT_DESCRIPTION}}"
DEPLOY_TO_AGENT_ENGINE = {{DEPLOY_TO_AGENT_ENGINE}}

# Ask for vars during script run.
PROJECT_ID = ""
REGION = ""
DATA_STORE_LOCATION = ""

# GitHub Constants.
REPOSITORY_NAME = "AgentSmithy"
# TODO: Set branch to release
REPOSITORY_BRANCH = "dev"
REPOSITORY_URL = "git@github.com:srastatter/AgentSmithy.git"

# Cloud Run services config.
BACKEND_PATH = "Runtime_env"
BACKEND_CONFIG_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{BACKEND_PATH}/deployment/config/{ENV_TAG}.yaml"
BACKEND_BUILD_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{BACKEND_PATH}/deployment/cd/{ENV_TAG}.yaml"
FRONTEND_PATH = "ChatbotUI"
FRONTEND_CONFIG_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{FRONTEND_PATH}/src/environments/environment.ts"
FRONTEND_BUILD_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{FRONTEND_PATH}/deployment/cd/{ENV_TAG}.yaml"

# Terraform Constants.
TERRAFORM_DIRECTORY = f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{BACKEND_PATH}/deployment/terraform"
TERRAFORM_VAR_FILE = "vars/env.tfvars"

# GCP resources constants.
ARTIFACT_REGISTRY_REPOSITORY = ""

CLOUD_RUN_BACKEND_SERVICE_NAME = AGENT_NAME.lower().replace(" ", "-") + "-backend"
CLOUD_RUN_FRONTEND_SERVICE_NAME = AGENT_NAME.lower().replace(" ", "-") + "-frontend"

CONFIGURATION_KEY_PROJECT = 'project'
CONFIGURATION_KEY_REGION = 'compute/region'

DATASTORE_INDUSTRY_SOURCES_MAP = {
    'finance': 'gs://cloud-samples-data/gen-app-builder/search/alphabet-investor-pdfs/*.pdf',
    'healthcare': 'gs://cloud-samples-data/vertex-ai/medlm/primock57/transcripts/*.txt',
    'retail': 'gs://cloud-samples-data/dialogflow-cx/google-store/*.html',
}
DATA_STORE_ID = 'agent_smithy_data_store_{}'.format(uuid4())
DATA_STORE_NAME = ""
SEARCH_APP_ENGINE_ID = 'agent_smithy_search_engine_{}'.format(uuid4())
GCS_STAGING_BUCKET = ""

def get_gcloud_default_configuration(config: str):
    """Attempts to get the default region from gcloud configuration."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", config],
            capture_output=True,
            text=True,
            check=True,
        )
        default_region = result.stdout.strip()
        if default_region:
            return default_region
        else:
            return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_user_input():
    """Prompts the user for GCP project, region, and AgentBuilder scope."""

    # 1. Project ID
    default_project_id = get_gcloud_default_configuration(CONFIGURATION_KEY_PROJECT)
    project_id_input = input(
        f"Press Enter to use the default project ID: '{default_project_id}', "
        "or enter a different project ID: "
    ).strip()
    project_id = project_id_input if project_id_input else default_project_id
    print(f"Using project ID: {project_id}")

    # 2. Region
    regions = [
        "africa-south1",
        "asia-east1",
        "asia-east2",
        "asia-northeast1",
        "asia-northeast2",
        "asia-northeast3",
        "asia-south1",
        "asia-south2",
        "asia-southeast1",
        "asia-southeast2",
        "australia-southeast1",
        "australia-southeast2",
        "europe-central2",
        "europe-north1",
        "europe-southwest1",
        "europe-west1",
        "europe-west10",
        "europe-west12",
        "europe-west2",
        "europe-west3",
        "europe-west4",
        "europe-west6",
        "europe-west8",
        "europe-west9",
        "me-central1",
        "me-central2",
        "me-west1",
        "northamerica-northeast1",
        "northamerica-northeast2",
        "northamerica-south1",
        "southamerica-east1",
        "southamerica-west1",
        "us-central1",
        "us-central2",
        "us-east1",
        "us-east4",
        "us-east5",
        "us-east7",
        "us-south1",
        "us-west1",
        "us-west2",
        "us-west3",
        "us-west4",
        "us-west8",
    ]

    region = get_gcloud_default_configuration(CONFIGURATION_KEY_REGION)
    print("\nAvailable GCP Regions:")
    for i, reg in enumerate(regions):
        print(f"{i+1}. {reg}")
    
    while True:
        try:
            default_region_choice = input(
                f"\nPress Enter to accept the default region ({region}), "
                "otherwise enter a number to choose from the available regions above."
            ).strip()
            if not default_region_choice: break
            retry_choice = int(default_region_choice) - 1
            if 0 <= retry_choice < len(regions):
                region = regions[retry_choice]
                print(f"Selected region: {region}")
                break
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a number.")
                    

    if region is None:
        print("No valid region selected. Exiting.")
        return None, None, None

    # 3. AgentBuilder Scope
    while True:
        agent_scope = input(
            "\nChoose the location for AgentBuilder resources (global, us, eu): "
        ).lower().strip()
        if agent_scope in ["global", "us", "eu"]:
            print(f"Using AgentBuilder location: {agent_scope}")
            break
        else:
            print("Invalid location. Please choose from 'global', 'us', or 'eu'.")

    return project_id, region, agent_scope


def clone(repo_url: str, branch: str):
    remove_command = ["rm", "-rf", REPOSITORY_NAME]
    subprocess.run(remove_command, check=True)

    clone_command = ["git", "clone", "-b", branch, repo_url]
    subprocess.run(clone_command, check=True)

def install_poetry_dependencies(pyproject_path_rel: str):
    """
    Installs dependencies from a pyproject.toml file using Poetry.

    Args:
        pyproject_path_rel: The relative path to the directory containing pyproject.toml.
    """
    # install poetry
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "poetry"])
        print("Poetry installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)  # Exit script if installation fails

    try:
        # Get the absolute path to the pyproject.toml directory
        absolute_path = os.path.abspath(pyproject_path_rel)
        command = [sys.executable, "-m", "poetry", "install", "--directory", absolute_path]
        subprocess.check_call(command)
        print("Poetry dependencies installed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error installing Poetry dependencies: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Poetry is not installed. Please install Poetry first.")
        sys.exit(1)

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
    return

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
    client = discoveryengine.EngineServiceClient(client_options=client_options)
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
    return

def run_agent_engine_deployment() -> str:
    # TODO figure out a better way to dynamically get these env after they are written
    navigate_to_directory(f"{REPOSITORY_NAME}/{BACKEND_PATH}")
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

    if not remote_agent.resource_name:
        raise Exception("Error deploying Agent to Agent Engine.")

    try:
        # If AGENT_ENGINE_RESOURCE_ID is set, then the agent will query the remote agent
        with open(BACKEND_CONFIG_FILE.replace(f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{BACKEND_PATH}/", ""), "a") as f:
            f.write(f"\nAGENT_ENGINE_RESOURCE_ID: {remote_agent.resource_name}\n")
        f.close()
    except FileNotFoundError:
        print(f"`{BACKEND_CONFIG_FILE.replace(f'{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{BACKEND_PATH}/', '')}` file not found.")

    navigate_to_directory(".")

    # Retrieve the project number associated with your project ID
    project_number = subprocess.run(
        ["gcloud", "projects", "describe", PROJECT_ID, '--format=value(projectNumber)'],
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


def get_cloud_run_url(project_id: str, region: str, service_name: str) -> str:
    try:
        describe = subprocess.run(["gcloud", "run", "services", "describe", service_name, "--project", project_id,"--region", region], capture_output=True, text=True)
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
            print(f"Error describing service (non-zero exit code):")
            print(f"Stdout: {describe.stdout}")
            print(f"Stderr: {describe.stderr}")
            return ""
    except Exception as e:  # Catch any other potential errors
        print(f"An unexpected error occurred: {e}")
        return ""

def configure_backend(
        gcs_bucket: str,
        datastore_id: str,
        frontend_url: str,
        config_file: str,
        project_id: str,
        region: str,
        agent_foundation_model: str,
        agent_industry_type: str,
        agent_orchestration_framework: str,
        agent_name: str,
        agent_description: str,
        data_store_location: str
):
    search_and_replace_file(config_file, r"GCS_STAGING_BUCKET:\s(.*?)*\n", f'GCS_STAGING_BUCKET: {gcs_bucket}\n')
    search_and_replace_file(config_file, r"DATA_STORE_ID:\s(.*?)*\n", f'DATA_STORE_ID: {datastore_id}\n')
    search_and_replace_file(config_file, r"FRONTEND_URL:\s(.*?)*\n", f'FRONTEND_URL: {frontend_url}\n')
    search_and_replace_file(config_file, r"PROJECT_ID:\s(.*?)*\n", f'PROJECT_ID: {project_id}\n')
    search_and_replace_file(config_file, r"VERTEX_AI_LOCATION:\s(.*?)*\n", f'VERTEX_AI_LOCATION: {region}\n')
    search_and_replace_file(config_file, r"AGENT_BUILDER_LOCATION:\s(.*?)*\n", f'AGENT_BUILDER_LOCATION: {data_store_location}\n')
    search_and_replace_file(config_file, r"AGENT_INDUSTRY_TYPE:\s(.*?)*\n", f'AGENT_INDUSTRY_TYPE: {agent_industry_type}\n')
    search_and_replace_file(config_file, r"AGENT_ORCHESTRATION_FRAMEWORK:\s(.*?)*\n", f'AGENT_ORCHESTRATION_FRAMEWORK: {agent_orchestration_framework}\n')
    search_and_replace_file(config_file, r"AGENT_FOUNDATION_MODEL:\s(.*?)*\n", f'AGENT_FOUNDATION_MODEL: {agent_foundation_model}\n')
    search_and_replace_file(config_file, r"USER_AGENT:\s(.*?)*\n", f'USER_AGENT: {agent_name}\n')
    search_and_replace_file(config_file, r"AGENT_DESCRIPTION:\s(.*?)*\n", f'AGENT_DESCRIPTION: {agent_description}\n')

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
        "--project",
        project_id,
        "--substitutions",
        f"_PROJECT_ID={project_id},_REGION={region},_CONTAINER_NAME={container_name},_ARTIFACT_REGISTRY_REPO_NAME={artifact_registry_name},_SERVICE_NAME={service_name}",
        f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{BACKEND_PATH}" if is_backend else f"{os.path.dirname(os.path.abspath(__file__))}/{REPOSITORY_NAME}/{FRONTEND_PATH}"
    ]
    subprocess.run(push_command, check=True)

def navigate_to_directory(directory: str):
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + f"/{directory}")

def search_and_replace_file(file_path: str, search_pattern: str, new_line: str):
    try:
        with open(file_path, "r") as f:
            file_content = f.read()
            updated_content = re.sub(search_pattern, new_line, file_content)
        with open(file_path, "w") as f:
            f.write(updated_content)
        f.close()
    except FileNotFoundError:
        print(f"`{file_path}` file not found.")

if __name__ == "__main__":
    project_id, region, datastore_location = get_user_input()

    if project_id and region and datastore_location:
        print("\n--- Configuration Summary ---")
        print(f"Project ID: {project_id}")
        print(f"Region: {region}")
        print(f"AgentBuilder location: {datastore_location}")

        PROJECT_ID = project_id
        REGION = region
        DATA_STORE_LOCATION = datastore_location
        
        ARTIFACT_REGISTRY_REPOSITORY = f"{PROJECT_ID.lower().replace(' ', '-')}-{AGENT_NAME.lower().replace(' ', '-')}-repository"
        DATA_STORE_NAME = f"{PROJECT_ID.lower().replace(' ', '-')}-{AGENT_NAME.lower().replace(' ', '-')}-datastore"
        GCS_STAGING_BUCKET = f"gs://{PROJECT_ID.lower().replace(' ', '-')}-agents-staging"

        # clone(REPOSITORY_URL, REPOSITORY_BRANCH)
        install_poetry_dependencies(f"{REPOSITORY_NAME}/{BACKEND_PATH}")

        from google.cloud import discoveryengine
        from google.api_core.client_options import ClientOptions
        import vertexai

        vertexai.init(
            project=PROJECT_ID,
            location=REGION,
            staging_bucket=GCS_STAGING_BUCKET
        )
        deploy_terraform_infrastructure(TERRAFORM_DIRECTORY, TERRAFORM_VAR_FILE)
        create_data_store()
        populate_data_store(AGENT_INDUSTRY_TYPE)
        create_search_app()

        # Build and deploy BE Service.
        frontend_url = get_cloud_run_url(PROJECT_ID, REGION, CLOUD_RUN_FRONTEND_SERVICE_NAME)
        configure_backend(
            GCS_STAGING_BUCKET,
            DATA_STORE_ID,
            frontend_url,
            BACKEND_CONFIG_FILE,
            PROJECT_ID,
            REGION,
            AGENT_FOUNDATION_MODEL,
            AGENT_INDUSTRY_TYPE,
            AGENT_ORCHESTRATION_FRAMEWORK,
            AGENT_NAME,
            AGENT_DESCRIPTION,
            DATA_STORE_LOCATION,
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
        backend_url = get_cloud_run_url(PROJECT_ID, REGION, CLOUD_RUN_BACKEND_SERVICE_NAME)
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
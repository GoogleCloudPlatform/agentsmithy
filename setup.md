# Environment Setup and Deployment Guide

This guide walks you through setting up your Google Cloud environment and deploying the Agent Bar v2 application to Cloud Run.

## 1. Infrastructure Setup (Terraform)

We use Terraform to automate the provisioning of all required Google Cloud resources.

### Before You Begin

Ensure you are logged into the Google Cloud CLI and have the correct project selected:

```bash
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
```

### Initialize and Apply Terraform

Navigate to the `deployment/terraform` directory and apply the configuration. This will enable all necessary APIs and create resources like storage buckets, service accounts, and the artifact registry.

```bash
cd deployment/terraform
```
```bash
terraform init
```
```bash
terraform apply -var="project_id=$(gcloud config get-value project)"
```
```bash
terraform plan --var="project_id=$(gcloud config get-value project)" -var-file=vars/dev.tfvars
```
```bash
# return the the main folder
cd ../..
```

*Terraform will provision:*
- **APIs**: AI Platform, Artifact Registry, Cloud Build, Cloud Run, etc.
- **Storage**: Buckets for default data, product ad generation, campaign manager, and meeting intelligence.
- **Artifact Registry**: A repository named `agent-bar-v2-repo` for your Docker images.
- **Service Account**: `agent-bar-v2-sa` with the required permissions.

## 2. Configure Environment Variables

After Terraform finishes, you need to configure your local `.env` file with the provisioned resource names.

Copy the sample environment file:
```bash
cp agent_bar_v2/.env.sample agent_bar_v2/.env
```

Retrieve the outputs from Terraform:
```bash
cd deployment/terraform
terraform output
cd ../..
```

Update `agent_bar_v2/.env` with the values from the `terraform output` command:
- `GOOGLE_CLOUD_PROJECT`: Use the `project_id` output.
- `GCS_BUCKET`: Use `gs://` followed by the `default_data_bucket_name` output.
- `GCS_BUCKET_PRODUCT_AD_GENERATION`: Use `gs://` followed by the `product_ad_generation_bucket_name` output.
- `GCS_BUCKET_CAMPAING_MANAGER`: Use the `campaign_manager_bucket_name` output.
- `GCS_BUCKET_MEETING_INTELLIGENCE`: Use the `meeting_intelligence_bucket_name` output.

## 4. Deploy to Cloud Run

Deploy the agent and its Web UI to Cloud Run using the `adk deploy cloud_run` command. We will use the Service Account created by Terraform.

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export SERVICE_ACCOUNT=$(cd deployment/terraform && terraform output -raw agent_service_account_email)
```

Generate cloud run required structure
```bash
cp deployment/cloud_run/requirements.txt .
cp deployment/cloud_run/Dockerfile .
cp deployment/cloud_run/main.py .

```

### Deploy the Agent Bar v2 application along with the UI
```bash
gcloud run deploy agent-bar-v2 \
--source . \
--region $REGION \
--project $PROJECT_ID \
--allow-unauthenticated \
--service-account $SERVICE_ACCOUNT \
--cpu=4 \
--memory=8Gi
--set-env-vars=$(grep -v '^#' agent_bar_v2/.env | xargs | sed 's/ /,/g')
# Add any other necessary environment variables your agent might need
```

## 5. Test Your Agent

Once deployed, you must initialize a session before interacting with the agent. Agent Bar v2 dynamically loads sub-agents and prompts based on the **Session State**.

### Initialize a Predefined Use Case

The `industry_id` and `use_case_id` are used to match a predefined agent configuration in the `agent_registry.py`.

```bash
# Get the deployed Cloud Run service URL
export CLOUD_RUN_URL=$(gcloud run services describe agent-bar-v2 --platform managed --region $REGION --format 'value(status.url)')

# Initialize a session for the "legal_guardian" use case in the "cross" industry
curl -X POST "$CLOUD_RUN_URL/apps/agent_bar_v2/users/user123/sessions/s_123" \
     -H "Content-Type: application/json" \
     -d '{ 
           "user_id": "user123", 
           "industry_id": "cross", 
           "use_case_id": "legal_guardian" 
         }'
```

### Initialize a Custom Agent Workflow

You can also bypass the registry and define a custom agent and workflow directly in the session state:

```bash
curl -X POST "$CLOUD_RUN_URL/apps/agent_bar_v2/users/user123/sessions/s_custom" \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "user123",
           "industry_id": "custom",
           "use_case_id": "my_workflow",
           "is_custom": true,
           "custom_agents": ["contract_review"],
           "custom_workflow_map": { "start": "contract_review", "contract_review": "end" },
           "custom_root_instructions": "You are a specialized assistant for reviewing legal contracts."
         }'
```

### Access the Web UI

After initializing the session via `curl`, you can interact with the agent in your browser:

```bash
echo "$CLOUD_RUN_URL/dev-ui/?app=agent_bar_v2&session=s_123&userId=user123"
```

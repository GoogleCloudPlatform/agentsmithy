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

### Ensure the required APIs are enabled:
These APIs are required for Terraform to manage the project reliably. If they are not already enabled, you'll need to enable them.
Once you enable the APIs via `gcloud`, wait about **30–60 seconds** before running `terraform apply`.
```bash
gcloud services enable \
    cloudresourcemanager.googleapis.com \
    serviceusage.googleapis.com \
    iam.googleapis.com
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

Automate the configuration of your `.env` file by running the following command. This pulls the provisioned resource names directly from Terraform and formats them for the application:

```bash
cd deployment/terraform


# 1. Get the Terraform outputs and save them to a temp file
terraform output -json | jq -r 'to_entries | .[] | "\(.key)=\(.value.value)"' > /tmp/tf_envs

# 2. Merge with .env.sample (parsing placeholders and overwriting TF outputs)
awk -F= 'NR==FNR{a[$1]=$2;next} {split($0,b,"="); key=b[1]; value=b[2]; if(value ~ /\[terraform_output:/){match(value,/\[terraform_output:[^\]]+\]/);hint=substr(value,RSTART+18,RLENGTH-19);if(hint in a){sub(/\[terraform_output:[^\]]+\]/,a[hint],value);print key"="value;next}} if(value ~ /\[your_project_id\]/){if("project_id" in a){sub(/\[your_project_id\]/,a["project_id"],value);print key"="value;next}} if(key in a){print key"="a[key];next} print $0}' /tmp/tf_envs ../../agent_bar_v2/.env.sample > ../../agent_bar_v2/.env

# 3. Clean up the temp file
rm /tmp/tf_envs


cd ../..
```

> **Note on Pre-loaded Data:** Some sub-agents (e.g., Knowledge Graph, Retail Inventory) require specific datasets or files to be pre-loaded into BigQuery or GCS. If an agent depends on pre-loaded data, you can find detailed instructions and schemas within that specific sub-agent's directory under `agent_bar_v2/subagents/`.

## 4. Deploy to Cloud Run

Deploy the agent and its Web UI to Cloud Run using the `gcloud run deploy` command. We will use the Service Account created by Terraform.

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export SERVICE_ACCOUNT=$(cd deployment/terraform && terraform output -raw agent_service_account_email)
```

### Temporarily bring the Dockerfile and main.py to the root
```bash
cp deployment/cloud_run/Dockerfile .
cp deployment/cloud_run/main.py .
```

### Deploy the Agent Bar v2 application along with the UI
```bash
gcloud run deploy agent-bar-v2 \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --service-account $SERVICE_ACCOUNT \
  --no-allow-unauthenticated \
  --cpu=4 \
  --memory=8Gi \
  --set-env-vars=$(grep -v '^#' agent_bar_v2/.env | xargs | sed 's/ /,/g')
# Add any other necessary environment variables your agent might need
```

# Clean up the root directory
```bash
rm Dockerfile main.py
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
     -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
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
     -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
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

### Access the Web UI (via Cloud Shell Proxy)

After initializing the session via `curl`, you can interact with the agent in your browser.

> [!NOTE]
> To ensure the Web UI uses the session you just initialized (e.g., `user123` / `s_123`), you should append them as query parameters to the URL in your browser.

```bash
# In a new Cloud Shell terminal tab, start the proxy:
gcloud run services proxy agent-bar-v2 --port=8080 --region us-central1

# Then, use the "Web Preview" button in the Cloud Shell toolbar
# and select "Preview on port 8080".
#
# To use your initialized session, append these to the URL:
# ?userId=user123&session=s_123
```

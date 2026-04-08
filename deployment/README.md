# Deployment

This directory contains the Terraform configurations for provisioning the necessary Google Cloud infrastructure for Multi-Agent Quest.

## Directory Structure

```text
deployment/
├── README.md
└── terraform/
    ├── apis.tf                 # Enables required Google Cloud APIs
    ├── artifact_registry.tf    # Provisions Docker repository for Multi-Agent Quest images
    ├── bigquery.tf             # Provisions BigQuery datasets and tables for FinOps, Knowledge Graph, and Retail
    ├── discoveryengine.tf      # Provisions Vertex AI Search (Discovery Engine) Datastores for FinOps and Retail
    ├── iam.tf                  # Provisions the Service Account and assigns required IAM roles
    ├── locals.tf               # Centralized local variables (APIs to enable, IAM roles list)
    ├── outputs.tf              # Defines the outputs (IDs, names, URLs) after applying Terraform
    ├── provider.tf             # Configures the Google Cloud provider
    ├── spanner.tf              # Provisions the Cloud Spanner instance and database for Knowledge Graph
    ├── storage.tf              # Provisions Cloud Storage buckets for various agents
    ├── variables.tf            # Declares all input variables
    └── vars/
        └── auto.tfvars         # Contains static values for the declared variables
```

## Provisioned Resources

The Terraform configurations in this directory will create the following Google Cloud resources:

### 1. APIs Enabled
- `aiplatform.googleapis.com` (Vertex AI)
- `artifactregistry.googleapis.com` (Artifact Registry)
- `cloudbuild.googleapis.com` (Cloud Build)
- `cloudresourcemanager.googleapis.com` (Cloud Resource Manager)
- `iam.googleapis.com` (Identity and Access Management)
- `storage.googleapis.com` (Cloud Storage)
- `speech.googleapis.com` (Cloud Speech-to-Text)
- `run.googleapis.com` (Cloud Run)
- `bigquery.googleapis.com` (BigQuery)
- `spanner.googleapis.com` (Cloud Spanner)
- `discoveryengine.googleapis.com` (Vertex AI Search and Conversation)

### 2. IAM & Service Accounts
- **Service Account**: `agent-bar-v2-sa`
- **Assigned Roles**:
  - `roles/aiplatform.user`
  - `roles/aiplatform.admin`
  - `roles/storage.admin`
  - `roles/logging.logWriter`
  - `roles/artifactregistry.reader`
  - `roles/bigquery.dataEditor`
  - `roles/bigquery.jobUser`
  - `roles/discoveryengine.editor`

### 3. Cloud Storage Buckets
- **Default Data**: `[PROJECT_ID]-abv2-agents-default-data`
- **Product Ad Generation**: `[PROJECT_ID]-abv2-cross-product-ad-generation`
- **Campaign Manager**: `[PROJECT_ID]-abv2-global-campaign-manager-agent`
- **Meeting Intelligence**: `[PROJECT_ID]-abv2-meeting-intelligence`
- **Macroeconomics**: `[PROJECT_ID]-abv2-macroeconomics`

### 4. Artifact Registry
- **Repository**: `agent-bar-v2-repo` (Docker format)

### 5. BigQuery Datasets & Tables
- **FinOps**:
  - Dataset: `finops`
  - Table: `finops10ktable`
- **Knowledge Graph**:
  - Dataset: `knowledge_graph_dataset`
- **Retail Inventory**:
  - Dataset: `retail_inventory`
  - Tables: `products`, `stores`, `inventory`
- **Finsights**:
  - Dataset: `finsights`
- **Cyber Guardian**:
  - Dataset: `cyber_guardian`

### 6. Vertex AI Search (Discovery Engine) Datastores
- **FinOps Data Store**: `finops-app-datastore` (GENERIC / NO_CONTENT)
- **Retail Support Data Store**: `retail-site-search-datastore` (GENERIC / NO_CONTENT)

## Usage

1. Navigate to the `terraform` directory: `cd deployment/terraform`
2. Initialize Terraform: `terraform init`
3. Review the planned changes: `terraform plan -var="project_id=YOUR_PROJECT_ID"`
4. Apply the configuration: `terraform apply -var="project_id=YOUR_PROJECT_ID"`

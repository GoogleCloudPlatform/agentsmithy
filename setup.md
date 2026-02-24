# Enviroment Setup

## Enable APIs
```
gcloud services enable \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    storage.googleapis.com
```

## Enrable requirements for sub agents
cross_industry/product_ad_generation requirements
```bash
LOCATION_ID=us-central1
gcloud storage buckets create --location=$LOCATION_ID gs://agent-bar-v2-cross-product-ad-generation

```

## Deploy

### Install ADK
```
python3 -m venv .venv
source .venv/bin/activate
pip install google-adk
```

### Deploy the agent
```
PROJECT_ID=ai-agent-bar-2026-stage
LOCATION_ID=us-central1

adk deploy agent_engine \
        --project=$PROJECT_ID \
        --region=$LOCATION_ID \
        --display_name="Agent Bar v2" \
        agent_bar_v2
```

### Test your agent

Create a session
```
RESOURCE_ID=<the reasoning engine resource id>
curl \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    "https://$(LOCATION_ID)-aiplatform.googleapis.com/v1/projects/$(PROJECT_ID)/locations/$(LOCATION_ID)/reasoningEngines/$(RESOURCE_ID):query" \
    -d '{"class_method": "async_create_session", "input": { "user_id": "123", "state": { "industry_id": "cross", "use_case_id": "legal_guardian", "root_prompt_overwrite":"New instructions here" }}}'
```
Chat
```
curl \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
https://$(LOCATION_ID)-aiplatform.googleapis.com/v1/projects/$(PROJECT_ID)/locations/$(LOCATION_ID)/reasoningEngines/$(RESOURCE_ID):query?alt=sse -d '{
"class_method": "async_stream_query",
"input": {
    "user_id": "u_123",
    "session_id": "4857885913439920384",
    "message": "Hey whats the weather in new york today?",
}
}'
```

Example:
```
RESOURCE_ID=3208589334617784320
curl \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    "https://us-central1-aiplatform.googleapis.com/v1/projects/ai-agent-bar-2026-dev/locations/us-central1/reasoningEngines/3208589334617784320:query" \
    -d '{"class_method": "async_create_session", "input": { "user_id": "123", "state": { "industry_id": "cross", "use_case_id": "legal_guardian", "root_prompt_overwrite":"" }}}'

curl \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
https://us-central1-aiplatform.googleapis.com/v1/projects/ai-agent-bar-2026-dev/locations/us-central1/reasoningEngines/3208589334617784320:streamQuery?alt=sse -d '{"class_method": "async_stream_query", "input": { "user_id": "123", "session_id": "53925685223227392", "message": "What you can do?"}}'
```


https://us-central1-aiplatform.googleapis.com/v1/projects/ai-agent-bar-2026-dev/locations/us-central1/reasoningEngines/3208589334617784320:streamQuery?alt=sse

https://us-central1-aiplatform.googleapis.com/v1/projects/ai-agent-bar-2026-stage/locations/us-central1/reasoningEngines/7140821147544715264:query

agent-bar-api-sa@ai-agent-bar-2026-stage.iam.gserviceaccount.com

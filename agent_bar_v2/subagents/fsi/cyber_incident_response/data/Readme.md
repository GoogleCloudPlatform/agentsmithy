# Cyber Incident Response Mock Data

> [!WARNING]
> This directory contains mock datasets for simulating cyber incidents, including references to malware tools (e.g., Mimikatz) and attack signatures in `endpoint_process_events.csv`. These files are for testing purposes only and do not contain live malware or sensitive data. They may trigger alerts in automated security scanners.

```bash
# Export required environment variables
export GOOGLE_CLOUD_PROJECT="[your-project-id]"
export BQ_DATASET="cyber_guardian_data" # Or your desired BigQuery dataset name
```

**4. Populate BigQuery Tables**
The required BigQuery tables can be populated from the provided CSV files. First, create the dataset, then load each table.

```bash
# Create the BigQuery dataset
bq --location=US mk --dataset ${GOOGLE_CLOUD_PROJECT}:${BQ_DATASET}

# Load data from CSV files into BigQuery
bq load --autodetect --source_format=CSV ${BQ_DATASET}.asset_inventory ./agent_bar_v2/subagents/fsi/cyber_incident_response/data/asset_inventory.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.endpoint_process_events ./agent_bar_v2/subagents/fsi/cyber_incident_response/data/endpoint_process_events.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.incident_management ./agent_bar_v2/subagents/fsi/cyber_incident_response/data/incident_management.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.network_connection_log ./agent_bar_v2/subagents/fsi/cyber_incident_response/data/network_connection_log.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.response_playbooks ./agent_bar_v2/subagents/fsi/cyber_incident_response/data/response_playbooks.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.threat_intelligence_kb ./agent_bar_v2/subagents/fsi/cyber_incident_response/data/threat_intelligence_kb.csv
```
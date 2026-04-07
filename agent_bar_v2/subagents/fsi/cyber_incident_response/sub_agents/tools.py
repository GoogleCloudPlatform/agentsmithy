# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
from datetime import datetime

from google.cloud import bigquery
from ..config import PROJECT_ID, CYBER_GUARDIAN_BQ_DATASET

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Helper Functions ---
def bq_rows_to_json(rows):
    """
    Converts BigQuery RowIterator to a JSON string.
    Handles potential serialization issues (e.g., datetime objects).
    """

    def datetime_converter(o):
        if isinstance(o, datetime):
            return o.isoformat()

    list_of_dicts = [dict(row) for row in rows]
    # Use the custom datetime_converter function in json.dumps
    return json.dumps(list_of_dicts, default=datetime_converter)


# --- Security Tools ---

def triageQueryTool(hostname: str, alert_type: str):
    """
    Queries initial logs for a given host to triage an alert.
    - Arg hostname: The hostname of the machine involved in the alert.
    - Arg alert_type: The type of alert ('EDR', 'NETWORK', 'LOGIN').
    """
    project_id = PROJECT_ID
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable not set")
    dataset = CYBER_GUARDIAN_BQ_DATASET
    client = bigquery.Client(project=project_id)

    table_name = {
        "EDR": "endpoint_process_events",
        "NETWORK": "network_connection_log",
        "LOGIN": "iam_login_events",
    }.get(alert_type, "endpoint_process_events")

    query = f"""
        SELECT * FROM `{project_id}.{dataset}.{table_name}`
        WHERE Hostname = @hostname
        ORDER BY EventTimestamp DESC
        LIMIT 5
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
        ]
    )

    try:
        rows = list(client.query(query, job_config=job_config).result())
        return bq_rows_to_json(rows)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error running triage query for {hostname}: {str(e)}"})


def investigationQueryTool(alert_type: str, hostname: str, parent_process: str = "", destination_ip: str = ""):
    """
    Performs a detailed investigation based on the alert type.
    - Arg alert_type: The type of alert ('EDR_DETECTION', 'IOC_MATCH', 'PHISHING_EMAIL').
    - Arg hostname: The hostname to investigate.
    - Arg parent_process: (Optional) The parent process for EDR alerts.
    - Arg destination_ip: (Optional) The malicious IP for IOC_MATCH alerts.
    """
    project_id = PROJECT_ID
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable not set")
    dataset = CYBER_GUARDIAN_BQ_DATASET
    client = bigquery.Client(project=project_id)

    if alert_type == "EDR_DETECTION":
        query = f"""
            SELECT EventTimestamp, ProcessName, CommandLine FROM `{project_id}.{dataset}.endpoint_process_events`
            WHERE Hostname = @hostname AND ParentProcessName = @parent_process
            ORDER BY EventTimestamp DESC LIMIT 10
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
                bigquery.ScalarQueryParameter("parent_process", "STRING", parent_process),
            ]
        )

    elif alert_type == "IOC_MATCH":
        query = f"""
            SELECT log_timestamp, source_ip, destination_ip, destination_port FROM `{project_id}.{dataset}.network_connection_log`
            WHERE source_host = @hostname AND destination_ip = @destination_ip
            ORDER BY log_timestamp DESC LIMIT 10
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
                bigquery.ScalarQueryParameter("destination_ip", "STRING", destination_ip),
            ]
        )
    else:
        return "Query did not match a known investigation type. Please provide more specific parameters."

    try:
        rows = list(client.query(query, job_config=job_config).result())
        return bq_rows_to_json(rows)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error running investigation query for {alert_type}: {str(e)}"})


# --- Threat Intel Tool ---
def threatIntelQueryTool(indicators: list[str]):
    """
    Checks indicators against a threat intelligence database (Simulated).
    - Arg indicators: A list of IPs, Domains, or Hashes.
    """
    try:
        # In a real scenario, this would call VirusTotal, CrowdStrike, or a local BQ table.
        intelligence_db = {
            "8.8.8.8": "benign",
            "1.2.3.4": "malicious - Known C2 Server",
            "malware.exe": "malicious - Ransomware Family X",
            "bad-domain.com": "malicious - Phishing Campaign Y",
        }
        results = {ind: intelligence_db.get(ind, "unknown") for ind in indicators}
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error querying threat intel database: {str(e)}"})


# --- Response Tools ---
def getPlaybookTool(triggering_condition: str):
    """
    Retrieves the response playbook for a given condition.
    - Arg triggering_condition: The type of threat (e.g., 'Ransomware', 'Phishing').
    """
    try:
        playbooks = {
            "EDR_DETECTION": "1. Isolate Host. 2. Kill malicious processes. 3. Scan for persistence. 4. Reset User Password.",
            "IOC_MATCH": "1. Block Destination IP at Firewall. 2. Identify all hosts contacting this IP. 3. Isolate affected hosts.",
            "PHISHING_EMAIL": "1. Purge email from all inboxes. 2. Identify users who clicked link. 3. Reset credentials for those users.",
        }
        return playbooks.get(triggering_condition, "Standard Triage: Gather more info and escalate to on-call.")
    except Exception as e:
        return f"Error retrieving playbook for '{triggering_condition}': {str(e)}"


def responseExecutionTool(action: str, target: str, requires_approval: bool = True):
    """
    Executes a response action on a target (Simulated).
    - Arg action: The action to perform ('Isolate Host', 'Block IP', 'Reset Password').
    - Arg target: The host or identifier to target.
    """
    try:
        if requires_approval:
            return f"Action '{action}' on '{target}' requested. Pending manual approval in the SOC portal."
        return f"Action '{action}' on '{target}' executed successfully."
    except Exception as e:
        return f"Error executing response action '{action}' on '{target}': {str(e)}"


def createIncidentTool(alert_type: str, hostname: str, user: str, severity: str):
    """
    Creates an incident ticket in the tracking system (Simulated).
    """
    try:
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Created incident {incident_id} for {alert_type} on {hostname}")
        return json.dumps({
            "status": "success",
            "incident_id": incident_id,
            "summary": f"Incident {severity} - {alert_type} detected on {hostname} for user {user}"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error creating incident ticket for {alert_type}: {str(e)}"})

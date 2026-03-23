# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Tools for the cyber incident response agent."""

from google.adk.tools import AgentTool
from .log_scanner.agent import root_agent as log_scanner_agent


def get_incident_contacts() -> list[dict]:
    """
    Returns a list of critical contacts for cyber incident response.
    """
    return [
        {"role": "CISO", "name": "Sarah Connor", "email": "sarah.connor@example.com", "phone": "+1-555-0100"},
        {"role": "Legal Counsel", "name": "Atticus Finch", "email": "atticus.finch@example.com", "phone": "+1-555-0101"},
        {"role": "PR/Comms", "name": "Don Draper", "email": "don.draper@example.com", "phone": "+1-555-0102"},
        {"role": "Cloud Provider Support", "name": "Tech Giant Corp", "email": "support@cloudprovider.com", "phone": "+1-800-555-0199"},
    ]


def get_impacted_systems() -> list[dict]:
    """
    Returns a list of critical systems that could be impacted by a cyber incident.
    """
    return [
        {"system": "Core Banking System", "owner": "John Doe", "email": "john.doe@example.com", "criticality": "High"},
        {"system": "Customer Portal", "owner": "Jane Smith", "email": "jane.smith@example.com", "criticality": "Medium"},
        {"system": "Trading Platform", "owner": "Bob Jones", "email": "bob.jones@example.com", "criticality": "High"},
        {"system": "Employee Payroll", "owner": "Alice Brown", "email": "alice.brown@example.com", "criticality": "Low"},
    ]


tools = [
    AgentTool(log_scanner_agent),
    get_incident_contacts,
    get_impacted_systems,
]

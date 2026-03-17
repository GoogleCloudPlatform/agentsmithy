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

"""Tools for the log scanner agent."""

import json
from .mock_logs import MOCK_LOGS

def get_logs(filter_ip: str = None) -> str:
    """
    Retrieves network logs, optionally filtering by source or destination IP.
    
    Args:
        filter_ip: Optional IP address to filter logs by.
        
    Returns:
        JSON string of filtered logs.
    """
    if filter_ip:
        filtered_logs = [
            log for log in MOCK_LOGS 
            if log.get("source_ip") == filter_ip or log.get("destination_ip") == filter_ip
        ]
        return json.dumps(filtered_logs, indent=2)
    return json.dumps(MOCK_LOGS, indent=2)


def get_unique_ips() -> str:
    """
    Retrieves a list of all unique IP addresses found in the logs.

    Returns:
        JSON string of unique IP addresses.
    """
    ips = set()
    for log in MOCK_LOGS:
        if "source_ip" in log:
            ips.add(log["source_ip"])
        if "destination_ip" in log:
            ips.add(log["destination_ip"])
    return json.dumps(list(ips), indent=2)

tools = [get_logs, get_unique_ips]

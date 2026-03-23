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

MOCK_LOGS = [
    {
        "timestamp": "2023-10-27T10:00:00Z",
        "source_ip": "192.168.1.10",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "SUCCESS",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:00Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "FAILURE",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:01Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "FAILURE",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:02Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "FAILURE",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:05:03Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "LOGIN_ATTEMPT",
        "status": "SUCCESS",
        "user": "admin"
    },
    {
        "timestamp": "2023-10-27T10:10:00Z",
        "source_ip": "203.0.113.42",
        "destination_ip": "10.0.0.5",
        "action": "DATA_EXFILTRATION",
        "status": "DETECTED",
        "details": "Large file transfer to external IP"
    }
]

#!/bin/bash
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
# Initialize a development session with the 'fsi' industry context
echo "Initializing session 's_125' with fsi context..."

curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_124/sessions/s_125 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "124", "industry_id": "fsi" }'

echo -e "\n\nDone! The session is ready.\nGo to the Web UI at: http://localhost:8000\nThen select 'agent_bar_v2' -> User 'u_124' -> Session 's_125'"

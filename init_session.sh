#!/bin/bash
# Initialize a development session with the 'fsi' industry context
echo "Initializing session 's_139' with fsi context..."

 

curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_139/sessions/s_139 \
-H "Content-Type: application/json" \
-d '{ "user_id": "139", "industry_id": "fsi", "use_case_id": "cyber_incident_response" }'

echo -e "\n\nDone! The session is ready.\nGo to the Web UI at: http://localhost:8000\nThen select 'agent_bar_v2' -> User 'u_139' -> Session 's_139'"

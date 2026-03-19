#!/bin/bash
# Initialize a development session with the 'fsi' industry context
echo "Initializing session 's_129' with fsi context..."

 

curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_133/sessions/s_133 \
-H "Content-Type: application/json" \
-d '{ "user_id": "133", "industry_id": "fsi", "use_case_id": "cyber_incident_response" }'

echo -e "\n\nDone! The session is ready.\nGo to the Web UI at: http://localhost:8000\nThen select 'agent_bar_v2' -> User 'u_124' -> Session 's_125'"

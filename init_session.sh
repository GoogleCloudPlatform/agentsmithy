#!/bin/bash
# Initialize a development session with the 'weather' industry context
echo "Initializing session 's_125' with weather context..."

curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_124/sessions/s_125 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "124", "industry_id": "weather" }'

echo -e "\n\nDone! The session is ready.\nGo to the Web UI at: http://localhost:8000\nThen select 'agent_bar_v2' -> User 'u_124' -> Session 's_125'"

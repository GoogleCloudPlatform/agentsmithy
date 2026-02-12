#!/bin/bash
# Initialize a development session with the 'finance' industry context
echo "Initializing session 's_123' with finance context..."

curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_123/sessions/s_123 \
     -H "Content-Type: application/json" \
     -d '{ "user_id": "123", "industry_id": "finance" }'

echo -e "\n\nDone! The session is ready.\nGo to the Web UI at: http://localhost:8000\nThen select 'agent_bar_v2' -> User 'u_123' -> Session 's_123'"

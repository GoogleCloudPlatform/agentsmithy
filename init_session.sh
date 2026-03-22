#!/bin/bash
# Initialize a development session with the 'fsi' industry context
echo "Initializing session 's_136' with fsi context..."

 

curl -X POST http://localhost:8000/apps/agent_bar_v2/users/u_136/sessions/s_136 \
-H "Content-Type: application/json" \
-d '{ "user_id": "136", "industry_id": "fsi", "use_case_id": "holistic_investment_strategy" }'

echo -e "\n\nDone! The session is ready.\nGo to the Web UI at: http://localhost:8000\nThen select 'agent_bar_v2' -> User 'u_136' -> Session 's_136'"

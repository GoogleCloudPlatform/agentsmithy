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

import json
import glob
import os

session_files = glob.glob('session-*.json')

for filepath in session_files:
    filename = os.path.basename(filepath)
    eval_filename = filename.replace('session-', 'eval-')
    eval_filepath = os.path.join('', eval_filename)
    
    with open(filepath, 'r') as f:
        session_data = json.load(f)
        
    app_name = session_data.get('appName', '')
    eval_set_id = app_name + "_eval"
    
    eval_case = {
        "eval_id": session_data.get('id', 'session_01'),
        "conversation": [],
        "session_input": {
            "app_name": app_name,
            "user_id": session_data.get('userId', 'user'),
            "state": session_data.get('state', {})
        }
    }
    
    # Maintain original invocation order
    invocation_ids = []
    invocations = {}
    for event in session_data.get('events', []):
        inv_id = event.get('invocationId')
        if not inv_id:
            continue
        if inv_id not in invocations:
            invocation_ids.append(inv_id)
            invocations[inv_id] = []
        invocations[inv_id].append(event)
        
    for inv_id in invocation_ids:
        events = invocations[inv_id]
        turn = {
            "invocation_id": inv_id,
            "user_content": None,
            "final_response": None,
            "intermediate_data": {
                "tool_uses": [],
                "tool_responses": [],
                "intermediate_responses": []
            }
        }
        
        for event in events:
            content = event.get('content', {})
            parts = content.get('parts', [])
            role = content.get('role')
            
            # user content (first text input from user)
            if event.get('author') == 'user' and not any('functionResponse' in p for p in parts) and not any('functionCall' in p for p in parts):
                turn['user_content'] = {
                    "parts": content.get("parts", []),
                    "role": "user"
                }
            
            # tool uses
            for p in parts:
                if 'functionCall' in p:
                    fc = p['functionCall']
                    turn['intermediate_data']['tool_uses'].append({
                        "id": fc.get('id', ''),
                        "args": fc.get('args', {}),
                        "name": fc.get('name', '')
                    })
                if 'functionResponse' in p:
                    fr = p['functionResponse']
                    turn['intermediate_data']['tool_responses'].append({
                        "id": fr.get('id', ''),
                        "name": fr.get('name', ''),
                        "response": fr.get('response', {})
                    })
            
            # final response (model text)
            if role == 'model' and any('text' in p for p in parts):
                turn['final_response'] = {
                    "parts": [{"text": p['text']} for p in parts if 'text' in p],
                    "role": "model"
                }
                
        eval_case["conversation"].append(turn)
        
    eval_data = {
        "eval_set_id": eval_set_id,
        "name": app_name.replace('_', ' ').title() + " Eval",
        "description": app_name.replace('_', ' ').title() + " Eval",
        "eval_cases": [eval_case]
    }
    
    with open(eval_filepath, 'w') as f:
        json.dump(eval_data, f, indent=2)

print("Eval files created.")
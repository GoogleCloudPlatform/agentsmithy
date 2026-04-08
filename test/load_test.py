# Copyright 2026 Google LLC
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

import asyncio
import aiohttp
import time
import subprocess
import json
import statistics
import os
from datetime import datetime

# Configuration
CONCURRENCY = 100
PROJECT_ID = "your_project_id" # "ai-agent-bar-2026-stage"
LOCATION = "your_location" # "us-central1"
# We'll use the ENGINE_ID from the previous run
ENGINE_ID = "your_agent_engine_id" # "5076999889058004992"
CREATE_SESSION_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}:query"
STREAM_QUERY_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}:streamQuery?alt=sse"

def get_access_token():
    try:
        result = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting gcloud token: {e}")
        print(e.stderr)
        raise

async def run_user_scenario(session, user_index, token, results):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    user_id = f"test_user_{user_index}"
    scenario_result = {
        "user_id": user_id,
        "success": False,
        "error": None,
        "duration": 0,
        "create_session": {
            "request": None,
            "response_status": None,
            "response_body": None,
            "error": None
        },
        "stream_query": {
            "request": None,
            "response_status": None,
            "response_body": [],
            "error": None
        }
    }
    
    start_time = time.time()
    try:
        # 1. Create session
        create_payload = {
            "class_method": "async_create_session", 
            "input": { 
                "user_id": user_id, 
                "state": { 
                    "industry_id": "cross", 
                    "use_case_id": "legal_guardian", 
                    "root_prompt_overwrite":"" 
                }
            }
        }
        scenario_result["create_session"]["request"] = create_payload
        
        async with session.post(CREATE_SESSION_URL, headers=headers, json=create_payload) as response:
            scenario_result["create_session"]["response_status"] = response.status
            
            if response.status != 200:
                text = await response.text()
                scenario_result["create_session"]["response_body"] = text
                scenario_result["create_session"]["error"] = f"HTTP {response.status}"
                scenario_result["error"] = f"Create session failed: {response.status} {text}"
                scenario_result["duration"] = time.time() - start_time
                results.append(scenario_result)
                return
                
            data = await response.json()
            scenario_result["create_session"]["response_body"] = data
            
            # Extract session_id robustly based on typical reasoning engine structures
            session_id = None
            if isinstance(data, dict):
                if "id" in data.get("output", {}):
                    session_id = str(data["output"]["id"])
                elif "session_id" in data.get("response", {}):
                    session_id = str(data["response"]["session_id"])
                elif "id" in data.get("response", {}):
                    session_id = str(data["response"]["id"])
                elif "session_id" in data:
                    session_id = str(data["session_id"])
                elif "id" in data:
                    session_id = str(data["id"])

            if not session_id:
                # Fallback
                session_id = str(data)
            
        # 2. Stream query
        stream_payload = {
            "class_method": "async_stream_query", 
            "input": { 
                "user_id": user_id, 
                "session_id": session_id, 
                "message": "What you can do?"
            }
        }
        scenario_result["stream_query"]["request"] = stream_payload
        
        async with session.post(STREAM_QUERY_URL, headers=headers, json=stream_payload) as response:
            scenario_result["stream_query"]["response_status"] = response.status
            
            if response.status != 200:
                text = await response.text()
                scenario_result["stream_query"]["response_body"] = text
                scenario_result["stream_query"]["error"] = f"HTTP {response.status}"
                scenario_result["error"] = f"Stream query failed: {response.status} {text}"
                scenario_result["duration"] = time.time() - start_time
                results.append(scenario_result)
                return
                
            # Read SSE stream
            chunks = []
            has_error = False
            error_message = None
            async for line in response.content:
                decoded = line.decode('utf-8')
                chunks.append(decoded)
                
                # The API returns HTTP 200 but a JSON payload with an error code for stream issues
                if not has_error and decoded.strip().startswith('{'):
                    try:
                        parsed = json.loads(decoded)
                        if parsed.get("code") and str(parsed.get("code")).startswith("4"):
                            has_error = True
                            error_message = parsed.get("message", decoded)
                    except json.JSONDecodeError:
                        pass
                        
            scenario_result["stream_query"]["response_body"] = chunks
            
            if has_error:
                scenario_result["stream_query"]["error"] = f"API Error: {error_message}"
                scenario_result["error"] = f"Stream API Error: {error_message}"
                scenario_result["duration"] = time.time() - start_time
                results.append(scenario_result)
                return
                
        scenario_result["duration"] = time.time() - start_time
        scenario_result["success"] = True
        results.append(scenario_result)
        
    except Exception as e:
        scenario_result["error"] = str(e)
        scenario_result["duration"] = time.time() - start_time
        results.append(scenario_result)

async def main():
    print("Fetching access token...")
    token = get_access_token()
    print("Token fetched. Starting load test with 100 concurrent users...")
    
    results = []
    
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=300) 
    
    start_time_global = time.time()
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for i in range(CONCURRENCY):
            tasks.append(asyncio.create_task(run_user_scenario(session, i, token, results)))
            
        await asyncio.gather(*tasks)
        
    total_time = time.time() - start_time_global
    
    # Save detailed results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_file = os.path.join(script_dir, f"load_test_results_{timestamp}.json")
    
    summary = {
        "concurrency": CONCURRENCY,
        "total_duration": total_time,
        "total_requests": len(results),
        "success_count": len([r for r in results if r["success"]]),
        "failure_count": len([r for r in results if not r["success"]]),
    }
    
    final_output = {
        "summary": summary,
        "results": results
    }
    
    with open(results_file, 'w') as f:
        json.dump(final_output, f, indent=2)
        
    print(f"\nDetailed results saved to {results_file}")
    
    # Calculate metrics
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    print("\n--- Load Test Results ---")
    print(f"Total Users Simulated: {CONCURRENCY}")
    print(f"Total Test Duration: {total_time:.2f} seconds")
    print(f"Successful Scenarios: {len(successes)}")
    print(f"Failed Scenarios: {len(failures)}")
    
    if successes:
        durations = [r["duration"] for r in successes]
        print("\n--- Latency Metrics (Successful only) ---")
        print(f"Min Latency: {min(durations):.2f}s")
        print(f"Max Latency: {max(durations):.2f}s")
        print(f"Avg Latency: {statistics.mean(durations):.2f}s")
        print(f"Median Latency: {statistics.median(durations):.2f}s")
        if len(durations) >= 2:
            try:
                durations.sort()
                index = int(0.95 * len(durations))
                print(f"95th Percentile: {durations[index]:.2f}s")
            except Exception:
                pass
        print(f"Requests per Second: {len(successes) / total_time:.2f} req/s")
        
    if failures:
        print("\n--- Errors ---")
        errors = list(set(r["error"] for r in failures))
        for error in errors[:5]:
            print(f"- {error}")
        if len(errors) > 5:
            print(f"... and {len(errors) - 5} more unique errors.")

if __name__ == "__main__":
    asyncio.run(main())
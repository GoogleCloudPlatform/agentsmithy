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

from google.adk.agents import LlmAgent
from injector import Injector
from ...data_lookup import DataProvider

def get_query_generation_agent(injector: Injector) -> LlmAgent:
    data_provider = injector.get(DataProvider)
    
    instruction=f"""
You are an experienced data analyst. Your task is to come up with a SQL
query using the {data_provider.dialect} SQL dialect.
The query should be used to answer the question provided by the business users.
The table name is "world_bank_data_2025" and it has the following schema where
the key is the column name and the value is the description of the column:
```json
{data_provider.get_schema()}
```
Be sure to use correct column names. Return ONLY the SQL query inside a ```sql code block.
"""

    return LlmAgent(
        model="gemini-2.5-flash",
        name="QueryGenerationAgent",
        description="Generates a SQL query from a natural language question.",
        instruction=instruction,
    )

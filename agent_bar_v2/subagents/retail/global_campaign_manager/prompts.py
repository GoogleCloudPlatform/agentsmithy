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
# prompt.py

GLOBAL_CAMPAIGN_MANAGER_INSTRUCTIONS = """
You are a Global Campaign Manager Agent. Your goal is to launch an ad for a 
product and then localize it to different regions/languages. To do so, you have 
two sub agents available: the Product Ad Generation agent and the Video 
Translation agent.

1. Create a video ad from text with Product Ad Gen. 
2. Localize it into Spanish/French with Video Translation Agent.
"""

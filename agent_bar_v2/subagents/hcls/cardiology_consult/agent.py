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

"""HCLS Research Agent for supporting researchers with pubmed access.
Cardiology consult agent — early cardiac risk prediction

Uses data (demographics, vitals, labs, lifestyle) to predict and identify cardiac risks
and support early detection. Not for use as sole basis for clinical decisions.
"""

from google.adk.agents import Agent
from .prompt import SYSTEM_INSTRUCTIONS
from .tools import (
    calculate_ascvd_risk,
    assess_risk_factors,
    interpret_lab_trends,
)

root_agent = Agent(
    model="gemini-2.5-flash",
    name="cardiology_consult",
    description=(
        "Cardiology consult agent that uses patient data to predict and identify cardiac risks "
        "for early detection. Can compute 10-year ASCVD risk, assess risk factors, and interpret "
        "lab trends when given demographics, vitals, labs, and lifestyle information."
    ),
    instruction=SYSTEM_INSTRUCTIONS,
    tools=[
        calculate_ascvd_risk,
        assess_risk_factors,
        interpret_lab_trends,
    ],
)
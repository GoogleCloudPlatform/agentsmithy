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

"""Tools for the Use Case Agent."""

from typing import Dict, Any

def calculate_metric(value: float, metric_type: str = "growth") -> Dict[str, Any]:
    """Calculates a specific metric based on the input value.

    Args:
        value: The base value to calculate from.
        metric_type: The type of metric (e.g., 'growth', 'retention'). Defaults to 'growth'.

    Returns:
        A dictionary containing the calculated metric details.
    """
    result = value * 1.5 if metric_type == "growth" else value * 0.8
    return {
        "metric": metric_type,
        "input_value": value,
        "calculated_result": result,
    }

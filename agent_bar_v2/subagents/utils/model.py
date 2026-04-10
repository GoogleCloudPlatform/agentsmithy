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

import os
from typing import Optional

from google.adk.models import Gemini
from google.genai import types


def get_gemini_config(temperature_override: Optional[float] = None) -> Gemini:
    """Dynamically resolves the Gemini model configuration with smart temperature defaults

    for Gemini 2.5 vs. Gemini 3 families.
    """
    model_version = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash")

    if temperature_override is not None:
        temperature = temperature_override
    else:
        fallback_temp = 1.0 if "gemini-3" in model_version else 0.5
        temperature = float(os.getenv("GEMINI_TEMPERATURE", fallback_temp))

    return Gemini(
        model=model_version,
        generation_config=types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=8192,
        ),
        retry_options=types.HttpRetryOptions(attempts=3),
    )

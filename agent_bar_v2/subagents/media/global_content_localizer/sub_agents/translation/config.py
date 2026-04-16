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
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
SPEECH_LOCATION = "us-central1" if LOCATION == "global" else LOCATION
BUCKET_NAME = os.getenv("GCS_BUCKET")
GCS_OUTPUT_PATH = "translation_agent_output"
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL_VERSION", "gemini-2.5-flash")
DEFAULT_SPEECH_MODEL = "chirp"
VALID_STT_MODELS = {"chirp", "chirp_2", "chirp_telephony"}

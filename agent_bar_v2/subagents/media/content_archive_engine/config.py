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

"""Configuration settings for the Use Case Agent."""

import os

# Google Cloud Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") #GOOGLE_CLOUD_PROJECT=ai-agent-bar-2026-stage
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION") #GOOGLE_CLOUD_LOCATION=us-central1
#GOOGLE_GENAI_USE_VERTEXAI=True
BUCKET_NAME = os.environ.get("GCS_BUCKET") #GCS_BUCKET=agent-catalog-media-data






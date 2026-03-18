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
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
PROJECT_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
BUCKET_NAME = os.environ.get("GCS_BUCKET")

BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID")
SPANNER_INSTANCE = os.environ.get("SPANNER_INSTANCE")
SPANNER_DATABASE = os.environ.get("SPANNER_DATABASE")
GRAPH_NAME = os.environ.get("GRAPH_NAME")

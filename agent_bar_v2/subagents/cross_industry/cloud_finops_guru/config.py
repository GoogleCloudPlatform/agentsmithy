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

import os

ROOT_AGENT_MODEL = os.getenv("ROOT_AGENT_MODEL")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")


BQ_DATA_PROJECT_ID = os.getenv("BQ_DATA_PROJECT_ID")

BQ_DATASET_ID = os.getenv("BQ_FINOPS_DATASET_ID")
BQ_TABLE_ID = os.getenv("BQ_TABLE_ID")
ACME_DATASTORE_ID = os.getenv("ACME_DATASTORE_ID","")
ROOT_AGENT_MODEL = os.getenv("ROOT_AGENT_MODEL","")
CODE_EXECUTOR_EXTENSION = os.environ.get("CODE_EXECUTOR_EXTENSION",None)

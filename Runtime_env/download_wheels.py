# Copyright 2025 Google LLC. All Rights Reserved.
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
# pylint: disable=C0301:line-too-long
"""Test Module for downloading Vertex AI Agent Framework"""
import subprocess
import os

WHEEL_URL = "gs://agent_framework/latest/google_genai_agents-0.0.2.dev20250304+733376416-py3-none-any.whl"
WHEEL_FILE = "google_genai_agents-0.0.2.dev20250204+723246417-py3-none-any.whl"

def download_wheel():
    """Downloads specified wheel file"""
    if not os.path.exists(WHEEL_FILE):
        try:
            subprocess.check_call(["gcloud", "storage", "cp", WHEEL_URL, "."])
            print(f"Downloaded {WHEEL_FILE}")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading wheel: {e}")
            raise

if __name__ == "__main__":
    download_wheel()

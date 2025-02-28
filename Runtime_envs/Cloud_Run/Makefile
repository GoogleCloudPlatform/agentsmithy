# Copyright 2025 Google LLC
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

ifneq (,$(wildcard ./deployment/env/local.dev.env))
    include deployment/env/local.dev.env
    export
endif

test:
	poetry run pytest tests/unit && poetry run pytest tests/integration

backend:
	poetry run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

load_test:
	poetry run locust -f tests/load_test/load_test.py -H $RUN_SERVICE_URL --headless -t 30s -u 60 -r 2 --csv=tests/load_test/.results/results --html=tests/load_test/.results/report.html

lint:
	poetry run codespell
	poetry run flake8 .
	poetry run pylint .
	poetry run mypy .
	poetry run black .

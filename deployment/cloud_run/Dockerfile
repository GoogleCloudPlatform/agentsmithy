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

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 1. Copy the config (now in the root context)
COPY pyproject.toml .

# 2. Install dependencies using the system python via uv
RUN uv pip install --system --no-cache .

# 3. Copy everything else into the container
COPY . .

# 4. Set Python path so it can find modules in subfolders
ENV PYTHONPATH=/app
ENV PORT=8080

RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

USER myuser
ENV PATH="/home/myuser/.local/bin:$PATH"

# 5. Run the app (main.py is now at the root)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
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
# pylint: disable=W0718, C0411
# ruff: noqa: I001

import json
import logging
import os
from typing import AsyncGenerator
import uuid

# from app.chain import chain
from app.orchestration.agent import AgentManager
from app.orchestration.config import (
    AGENT_INDUSTRY_TYPE,
    AGENT_ORCHESTRATION_FRAMEWORK
)
from app.orchestration.utils import get_init_prompt
from app.utils.input_types import Feedback, Input, InputChat, default_serialization
from app.utils.output_types import EndEvent, Event
from app.utils.tracing import CloudTraceLoggingSpanExporter
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import logging as google_cloud_logging
from traceloop.sdk import Instruments, Traceloop

# The events that are supported by the UI Frontend
SUPPORTED_EVENTS = [
    "on_chat_model_stream",
]

# Initialize FastAPI app and logging
app = FastAPI()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)

def configure_cors(app):
    if not os.getenv("FRONTEND_URL"):
        url = "http://localhost:4200"
    else:
        url = os.getenv("FRONTEND_URL")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Initialize Traceloop
try:
    Traceloop.init(
        app_name="Sample Chatbot Application",
        disable_batch=False,
        exporter=CloudTraceLoggingSpanExporter(),
        instruments={Instruments.VERTEXAI, Instruments.LANGCHAIN},
    )
except Exception as e:
    logging.error("Failed to initialize Traceloop: %s", e)

# Set up the agent backed on environment variables for user config
init_prompt = get_init_prompt(AGENT_INDUSTRY_TYPE)
agent = AgentManager(
    prompt=init_prompt,
    orchestration_framework=AGENT_ORCHESTRATION_FRAMEWORK
)
# print(agent.tools)

async def stream_event_response(input_chat: InputChat) -> AsyncGenerator[str, None]:
    """Stream events in response to an input chat."""
    run_id = uuid.uuid4()
    input_dict = input_chat.model_dump()

    Traceloop.set_association_properties(
        {
            "log_type": "tracing",
            "run_id": str(run_id),
            "user_id": input_dict["user_id"],
            "session_id": input_dict["session_id"],
            "commit_sha": os.environ.get("COMMIT_SHA", "None"),
        }
    )

    yield json.dumps(
        Event(event="metadata", data={"run_id": str(run_id)}),
        default=default_serialization,
    ) + "\n"

    # async for data in chain.astream_events(input_dict, version="v2"):
    #     if data["event"] in SUPPORTED_EVENTS:
    #         yield json.dumps(data, default=default_serialization) + "\n"

    async for data in agent.astream(input_dict):
        yield json.dumps(data, default=default_serialization) + "\n"

    yield json.dumps(EndEvent(), default=default_serialization) + "\n"


# Routes
@app.get("/")
async def redirect_root_to_docs() -> RedirectResponse:
    """Redirect the root URL to the API documentation."""
    return RedirectResponse("/docs")


@app.post("/feedback")
async def collect_feedback(feedback_dict: Feedback) -> None:
    """Collect and log feedback."""
    logger.log_struct(feedback_dict.model_dump(), severity="INFO")


@app.post("/chats")
async def stream_chat_events(request: Input) -> StreamingResponse:
    """Stream chat events in response to an input request."""
    return StreamingResponse(
        stream_event_response(input_chat=request.input), media_type="text/event-stream"
    )

configure_cors(app)

# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
from google.adk.tools import VertexAiSearchTool

from ...config import ACME_DATASTORE_ID

acme_search_tool = VertexAiSearchTool(data_store_id=ACME_DATASTORE_ID)

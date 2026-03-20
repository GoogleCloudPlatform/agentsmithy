# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Defines tools for Catalog Enrichment agent."""

import logging
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from google.adk.tools import ToolContext
from google.cloud import bigquery

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize BigQuery client outside the function
client: bigquery.Client | None = None
try:
    client = bigquery.Client()
except Exception as e:
    logger.error(f"Error initializing BigQuery client: {e}")
    client = None

# GCP table information
GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
GCP_DATASET_ID = os.getenv("GCP_DATASET_ID")
GCP_PRODUCT_TABLE_ID = os.getenv("GCP_PRODUCT_TABLE_ID")


def search_catalog(tool_context: ToolContext, search_term: str) -> str:
    """
    Searches the product catalog to verify existing products or find products to enrich.

    Args:
        search_term (str): The product name or ID to search for.

    Returns:
        markdown_table (str): A markdown table containing product details, or an error message if
        BigQuery client initialization has failed or no results are found.
    """
    if client is None:
        logger.error("BigQuery client initialization failed.")
        return "BigQuery client initialization failed."

    query = f"""
    SELECT
        product_name,
        uniq_id,
        brand,
        list_price
    FROM
        `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.{GCP_PRODUCT_TABLE_ID}`
    WHERE 
        UPPER(product_name) LIKE UPPER(CONCAT('%', @search_term_placeholder, '%'))
        OR UPPER(uniq_id) = UPPER(@search_term_placeholder)
    LIMIT 10
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("search_term_placeholder", "STRING", search_term),
        ]
    )

    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        # Check if there are any rows in the result iterator
        if results.total_rows == 0:
            return "No products found matching the search term."

        markdown_table = "| Index | Product Name | Product ID | Brand | List Price |\n"
        markdown_table += "|--------------|--------------|--------------|-------|------------|\n"

        for i, row in enumerate(results):
            product_name = row.product_name
            product_id = row.uniq_id
            brand = row.brand
            list_price = row.list_price

            markdown_table += f"| {i} | {product_name} | {product_id} | {brand} | {list_price} |\n"

        return markdown_table
    except Exception as e:
        logger.error(f"Error querying catalog: {e}")
        return f"Error executing search query: {e}"


def add_product_to_catalog(
    tool_context: ToolContext, 
    product_name: str, 
    brand: str, 
    list_price: float, 
    description: str,
    uniq_id: Optional[str] = None
) -> str:
    """
    Simulates inserting a new enriched product into the catalog table in BigQuery.
    The item will be displayed for review before being added to the database.

    Args:
        product_name (str): The name of the product.
        brand (str): The brand of the product.
        list_price (float): The list price of the product.
        description (str): The enriched description of the product.
        uniq_id (Optional[str]): The unique ID of the product. If not provided, a UUID will be generated.

    Returns:
        review_message (str): A markdown table containing the product details to be reviewed.
    """
    if uniq_id is None:
        uniq_id = str(uuid.uuid4())

    markdown_table = "### Pending Catalog Enrichment Review\n"
    markdown_table += "The following product has been staged for review before being added to the catalog table:\n\n"
    markdown_table += "| Product Name | Product ID | Brand | List Price | Description |\n"
    markdown_table += "|--------------|--------------|-------|------------|-------------|\n"
    
    # We truncate the description in the table to keep it readable, but the full description would be saved
    truncated_desc = description[:50] + "..." if len(description) > 50 else description
    
    markdown_table += f"| {product_name} | {uniq_id} | {brand} | {list_price} | {truncated_desc} |\n"

    logger.info(f"Staged product {product_name} with ID {uniq_id} for review.")
    return markdown_table


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

"""Defines tools for NL2SQL agent."""

import logging
import os
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

# GCP table information (move this to .env file in the future) + have this more
# generic to be able to work outside of this project (possibly Terraform)
GCP_PROJECT_ID = os.getenv("BQ_DATA_PROJECT_ID")
GCP_DATASET_ID = os.getenv("GCP_DATASET_ID")
GCP_PRODUCT_TABLE_ID = os.getenv("GCP_PRODUCT_TABLE_ID")
GCP_STORE_TABLE_ID = os.getenv("GCP_STORE_TABLE_ID")
GCP_INVENTORY_TABLE_ID = os.getenv("GCP_INVENTORY_TABLE_ID")


def search_product_table(tool_context: ToolContext, search_type: str) -> str:
    """
    Searches for a brand from a BigQuery table and returns a list of products
    that match the search.

    Args:
        search_type (str): Either 'product' or 'brand' which indicates what the user wants to search for.

    Returns:
        markdown_table (str): A markdown table containing product details, or an error message if
        BigQuery client initialization has failed.
    """
    try:
        if tool_context.user_content and tool_context.user_content.parts:
            search_term = tool_context.user_content.parts[0].text
        else:
            logger.error("User content is missing or malformed.")
            return "User content is missing or malformed."

        if client is None:
            logger.error("BigQuery client initialization failed.")
            return "BigQuery client initialization failed."

        if search_type == "product":
            query = f"""
            SELECT
                product_name,
                uniq_id,
                brand,
                list_price
            FROM
                `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.{GCP_PRODUCT_TABLE_ID}`
            WHERE UPPER(product_name) LIKE UPPER(CONCAT('%', @search_term_placeholder, '%'))
            """
        elif search_type == "brand":
            query = f"""
            SELECT
                product_name,
                uniq_id,
                brand,
                list_price
            FROM
                `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.{GCP_PRODUCT_TABLE_ID}`
            WHERE UPPER(brand) LIKE UPPER(CONCAT('%', @search_term_placeholder, '%'))
            """
        else:
            return "Invalid search type. Use 'product' or 'brand'."

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("search_term_placeholder", "STRING", search_term),
            ]
        )

        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        markdown_table = "| Index | Product Name | Product ID | Brand | List Price |\n"
        markdown_table += "|--------------|--------------|--------------|-------|------------|\n"

        i = 0
        for row in results:
            product_name = row.product_name
            product_id = row.uniq_id
            brand = row.brand
            list_price = row.list_price

            tool_context.state[f"row_{i}"] = {}
            tool_context.state[f"row_{i}"]["product_name"] = product_name
            tool_context.state[f"row_{i}"]["product_id"] = product_id
            tool_context.state[f"row_{i}"]["brand"] = brand
            tool_context.state[f"row_{i}"]["list_price"] = list_price

            markdown_table += f"| {i} | {product_name} | {product_id} | {brand} | {list_price} |\n"

            i += 1

        return markdown_table
    except Exception as e:
        return f"Error in search_product_table: {e}"


def search_product_table_v2(tool_context: ToolContext, search_term: str, filter: Optional[str] = None) -> str:
    """
    Searches for a brand from a BigQuery table and returns a list of products
    that match the search. Uses BQML semantic similarity search.

    Args:
        search_term (str): The term or phrase the user wants to search for, used in the similarity search in the BQ query.
        filter (str, optional): Price filter that the user can specify for filtering for above or below a given dollar value. Defaults to None.

    Returns:
        markdown_table (str): A markdown table containing product details, or an error message if
        BigQuery client initialization has failed.
    """
    try:
        if client is None:
            logger.error("BigQuery client initialization failed.")
            return "BigQuery client initialization failed."

        query = f"""
        WITH query_embeddings AS(
        SELECT
            ml_generate_embedding_result.*
        FROM
            ML.GENERATE_EMBEDDING(
            MODEL `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.text_embedding`,
            (SELECT @search_term_placeholder AS content)
            ) AS ml_generate_embedding_result
        ),
        distances AS (
        SELECT
            product_name,
            uniq_id,
            brand,
            list_price,
            ML.DISTANCE(text_embedding, (SELECT ml_generate_embedding_result FROM query_embeddings), 'COSINE') AS distance
        FROM
            `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.{GCP_PRODUCT_TABLE_ID}`
        WHERE text_embedding IS NOT NULL AND
            ML.DISTANCE(text_embedding, (SELECT ml_generate_embedding_result FROM query_embeddings), 'COSINE') < 1
        )
        SELECT
            product_name,
            uniq_id,
            brand,
            list_price
        FROM
            distances
        WHERE
            CASE
                WHEN @filter_param = 'equals' THEN list_price = @price_placeholder
                WHEN @filter_param = 'less_than' THEN list_price < @price_placeholder
                WHEN @filter_param = 'greater_than' THEN list_price > @price_placeholder
                ELSE 1 = 1
            END
        ORDER BY
            distance ASC
        LIMIT 10
        """

        if filter:
            try:
                filter_split = filter.split()
                if filter_split[1] == "<":
                    operator = "less_than"
                elif filter_split[1] == ">":
                    operator = "greater_than"
                else:
                    operator = "equals"
            except Exception as e:
                logger.error(f"Error parsing filter: {e}")
                return "There was an error with the pricing filter. Please provide a new search query"

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("search_term_placeholder", "STRING", search_term),
                    bigquery.ScalarQueryParameter("filter_param", "STRING", operator),
                    bigquery.ScalarQueryParameter("price_placeholder", "FLOAT", filter_split[2]),
                ]
            )
        else:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("search_term_placeholder", "STRING", search_term),
                    bigquery.ScalarQueryParameter("filter_param", "STRING", None),
                    bigquery.ScalarQueryParameter("price_placeholder", "FLOAT", None),
                ]
            )

        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        markdown_table = "| Index | Product Name | Product ID | Brand | List Price |\n"
        markdown_table += "|--------------|--------------|--------------|-------|------------|\n"

        i = 0
        for row in results:
            product_name = row.product_name
            product_id = row.uniq_id
            brand = row.brand
            list_price = row.list_price

            tool_context.state[f"row_{i}"] = {}
            tool_context.state[f"row_{i}"]["product_name"] = product_name
            tool_context.state[f"row_{i}"]["product_id"] = product_id
            tool_context.state[f"row_{i}"]["brand"] = brand
            tool_context.state[f"row_{i}"]["list_price"] = list_price

            markdown_table += f"| {i} | {product_name} | {product_id} | {brand} | {list_price} |\n"

            i += 1

        return markdown_table
    except Exception as e:
        return f"Error in search_product_table_v2: {e}"


def product_selection(tool_context: ToolContext, index: str) -> str:
    selection = f"row_{index}"
    row = tool_context.state[selection]

    markdown_table = "| Index | Product Name | Product ID | Brand | List Price |\n"
    markdown_table += "|--------------|--------------|--------------|-------|------------|\n"
    markdown_table += (
        f"| {index} | {row['product_name']} | {row['product_id']} | {row['brand']} | {row['list_price']} |\n"
    )

    tool_context.state["selected_product_id"] = ""
    tool_context.state["selected_product_id"] = row["product_id"]
    logger.info(f"Added product_id={selection} to state")

    return markdown_table


def store_locator(tool_context: ToolContext) -> str:
    """
    Searches for the product SKU to check if it is in stock in stores close to
    the user.

    Args:
        product_name (str): The name of the product to search for.

    Returns:
        None
    """
    try:
        if client is None:
            return "BigQuery client initialization failed."

        product_id = tool_context.state.get("selected_product_id", 0)
        logger.info(f"selected_product_id={product_id}, type={type(product_id)}")
        product_id = str(product_id)

        query = f"""
        SELECT
            inventory.store_id,
            inventory.uniq_id,
            inventory.inventory,
            store.name,
            store.url,
            store.city,
            store.state
        FROM
            `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.{GCP_INVENTORY_TABLE_ID}` inventory
        LEFT JOIN
            `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.{GCP_STORE_TABLE_ID}` store
        ON
            inventory.store_id = store.store_id
        WHERE
            inventory.uniq_id = @product_id_placeholder
        LIMIT 10
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("product_id_placeholder", "STRING", product_id),
            ]
        )

        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        markdown_table = "| Store Name | City | State | Inventory |\n"
        markdown_table += "|--------------|---------------|---------------|------------|\n"

        for row in results:
            store_name = row.name
            city = row.city
            state = row.state
            inventory = row.inventory

            markdown_table += f"| {store_name} | {city} | {state} | {inventory} |\n"

        return markdown_table
    except Exception as e:
        return f"Error in store_locator: {e}"


def place_order(tool_context: ToolContext, store_id: str, product_id: str) -> None:
    """
    Places order for the product SKU in the specific store the user selectd.

    Args:
        store_id (str): ID of the store selected.
        product_id (str): SKU of the product selected.

    Returns:
        None
    """
    # TODO: implement the place order functionality
    return None

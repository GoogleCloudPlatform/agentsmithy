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

"""Tools for the medical_search_agent."""

import time
from io import StringIO
import os
import certifi

from Bio import Entrez, Medline

os.environ['SSL_CERT_FILE'] = certifi.where()

def search_pubmed(
    search_string: str,
    limit: int,
    email: str = "no-reply@google.com",
) -> list:
    """
    Fetches articles with abstracts for a search_string from pubmed.

    Required Args:
        search_string: The string for the search (e.g., "Treatment for KRAS G13D Breast Cancer")
        limit: The maximum number of articles to fetch

    Returns:
        On success: A list of dictionaries with the PMID id as key and a dictionary of
        the Medline content as value.
        On error: A list containing the error of the search, either "Error connecting to Pubmed"
        or "Could not find any articles"
    """
    print(
        f"--- Tool called: Fetching {limit} articles for {search_string} via Pubmed API ---"
    )
    # Always provide an email to identify yourself to the API.
    # This is a requirement from NCBI.
    Entrez.email = email  # type: ignore

    # Use Entrez.esearch to perform the search
    try:
        handle = Entrez.esearch(db="pubmed", term=search_string, retmax=limit)
        id_list = Entrez.read(handle)["IdList"]
        handle.close()
    except ConnectionError as e:
        return [f"Error connecting to Pubmed: {e}"]

    records = []

    # If id_list is empty
    if not id_list:
        return ["Could not find any articles"]

    # Use Entrez.efetch to retrieve the full details of the articles
    # Convert from
    for id in id_list:
        try:
            handle = Entrez.efetch(
                db="pubmed", id=id, rettype="medline", retmode="text"
            )
            data = handle.read()
            handle.close()
            record = list(Medline.parse(StringIO(data)))
            records.append(
                {
                    "pmid": id,
                    "article": record,
                }
            )
        except ConnectionError as e:
            return [f"Error connecting to Pubmed: {e}"]

        time.sleep(1)

    return records

tools = [search_pubmed]

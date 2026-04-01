# Copyright 2026 Google LLC. All Rights Reserved.
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

import sqlite3
import pandas as pd
import aiosqlite
from pathlib import Path
from typing import Any, List
import json
from pydantic import BaseModel

class DataSource(BaseModel):
    name: str
    description: str
    columns: dict

class DataProvider:
    """Provider for macro economic data from a SQLite database."""
    def __init__(self, csv_data: str | Path, db_path: str | Path | None = None) -> None:
        self.csv_data = csv_data
        self.db_path = "file::memory:?cache=shared" if db_path is None else str(db_path)
        
        # Maintain a keep-alive connection for in-memory DB with shared cache
        self._keep_alive_conn = sqlite3.connect(self.db_path, uri=True)
        
        # Handle table name from GCS URI or local Path
        if isinstance(csv_data, str) and csv_data.startswith("gs://"):
            self.table_name = Path(csv_data.split("/")[-1]).stem
        else:
            self.table_name = Path(csv_data).stem
            
        self._load_data_from_csv(csv_data)
        
        self.data_sources = [
            DataSource(
                name=self.table_name,
                description="Macroeconomic data including GDP, inflation, and unemployment for various countries.",
                columns={
                    "country_name": "Full name of the country",
                    "country_id": "ISO 3166-1 alpha-2 code",
                    "year": "Calendar year",
                    "inflation": "Consumer Price Index (annual %)",
                    "gdp": "Gross Domestic Product (current US$)",
                    "gdp_per_capita": "GDP per capita (current US$)",
                    "unemployment_rate": "Unemployment, total (% of total labor force)",
                    "interest_rate": "Real interest rate (%)",
                    "inflation_gdp_deflator": "Inflation, GDP deflator (annual %)",
                    "gdp_growth": "GDP growth (annual %)",
                    "current_account_balance": "Current account balance (% of GDP)",
                    "government_expense": "Expense (% of GDP)",
                    "government_revenue": "Revenue, excluding grants (% of GDP)",
                    "tax_revenue": "Tax revenue (% of GDP)",
                    "gross_national_income": "GNI (current US$)",
                    "public_debt": "Central government debt, total (% of GDP)"
                }
            )
        ]

    def _load_data_from_csv(self, csv_path: str | Path) -> None:
        df = pd.read_csv(csv_path)
        # Use simple sqlite3 for initial load
        conn = sqlite3.connect(self.db_path, uri=True)
        df.to_sql(self.table_name, conn, if_exists="replace", index=False)
        conn.close()

    @property
    def dialect(self) -> str:
        return "sqlite"

    def get_schema(self) -> str:
        return json.dumps([source.model_dump() for source in self.data_sources], indent=2)

    async def fetch_data(self, query: str) -> List[Any]:
        async with aiosqlite.connect(self.db_path, uri=True) as db:
            async with db.execute(query) as cursor:
                return await cursor.fetchall()

    async def validate_query(self, query: str) -> bool:
        """Simple validation by explaining the query."""
        try:
            async with aiosqlite.connect(self.db_path, uri=True) as db:
                await db.execute(f"EXPLAIN {query}")
                return True
        except Exception:
            return False

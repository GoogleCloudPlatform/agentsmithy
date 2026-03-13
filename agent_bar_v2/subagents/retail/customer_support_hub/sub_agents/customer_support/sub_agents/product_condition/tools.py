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

"""Defines the tools for the Product Condition Agent."""

import os
import re

dir_path = os.path.dirname(os.path.relpath(__file__))


def get_all_store_data() -> str:
    """
    Returns the availables store locations and their associated information.

    Returns:
        A string containing all store data in CSV format.
    """
    file_name = os.path.join(dir_path, "data/store_locations.csv")
    try:
        with open(file_name, "r") as f:
            return f.read()
    except Exception as e:
        return f"An error occurred while reading the store data: {e}"


def is_valid_email(email: str) -> bool:
    """Check if the email is a valid format.

    Args:
        email (str). Email address

    Returns:
        True if the email is valid, False otherwise.
    """

    regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$"
    if re.match(regex, email):
        return True
    else:
        return False

tools = [
    get_all_store_data,
    is_valid_email
]

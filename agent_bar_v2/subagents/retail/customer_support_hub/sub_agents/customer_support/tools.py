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

"""Defines tools for the Router Agent"""

from .sub_agents.product_condition.agent import root_agent as product_condition_agent
from .sub_agents.refund_issue.agent import root_agent as refund_issue_agent
from google.adk.tools import AgentTool
import os
import re

dir_path = os.path.dirname(os.path.relpath(__file__))

def escalation_contact_number() -> str:
    """Provides contact number to transfer and escalate
    issues to human customer support.

    Returns:
        Contact phone number.
    """

    return "888-000-0000"

def get_all_store_data() -> str:
    """
    Returns the availables store locations and their associated information in csv format.

    Returns:
        A string containing all store data in CSV format.
    """
    # file_name = os.path.join(dir_path, "data/store_locations.csv")
    # try:
    #     with open(file_name, "r") as f:
    #         return f.read()
    # except Exception as e:
    #     return f"An error occurred while reading the store data: {e}"

    stores_details="""
store_name,city,zipcode,hours
City Grocers,New York,10002,"Mon-Fri: 8am-9pm, Sat-Sun: 9am-7pm"
Flagship Store,New York,10001,"Mon-Fri: 8am-10pm, Sat-Sun: 9am-8pm"
Super Mart,Los Angeles,90001,"Mon-Sat: 7am-10pm, Sun: 8am-8pm"
Fresh Finds,Chicago,60614,"Mon-Sat: 9am-9pm, Sun: Closed"
City Center,Chicago,60601"Mon-Sun: 8am-10pm"
    """
    return stores_details

def is_valid_email(email: str) -> bool:
    """Check if the email is a valid format.

    Args:
        email (str). Email address

    Returns:
        True if the email is valid, False otherwise.
    """

    try:
        regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$"
        if re.match(regex, email):
            return True
        else:
            return False
    except Exception:
        return False

product_condition_agent, refund_issue_agent
tools = [
    escalation_contact_number,
    get_all_store_data,
    is_valid_email,
    AgentTool(product_condition_agent),
    AgentTool(refund_issue_agent)
]

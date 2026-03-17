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

"""Defines the tools for the Refund Issue Agent."""


def refund_lookup_tool(order_number: str) -> str:
    """Retrieves refund status based on associated order number.

    Args:
        order_number: order identifier associated with the refund request.
        It is a six-digit number.

    Returns:
        Refund status.
    """
    try:
        if len(order_number) < 6:
            return "Invalid order number"

        number = int(order_number)

        if number > 0 and number < 100000:
            status = "Refund issued"
        elif number >= 100000 and number <= 999999:
            status = "Return pending"
        else:
            status = "Invalid order number"
    except Exception:
        return "Invalid order number"

    return status

tools = [
    refund_lookup_tool
]

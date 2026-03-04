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

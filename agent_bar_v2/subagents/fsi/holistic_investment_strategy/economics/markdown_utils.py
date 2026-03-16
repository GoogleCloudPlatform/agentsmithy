import re

def extract_sql_from_markdown(text: str) -> str:
    """Extracts SQL code from a markdown code block."""
    match = re.search(r"```sql\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

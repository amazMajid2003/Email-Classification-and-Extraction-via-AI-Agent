import re
from bs4 import BeautifulSoup


def clean_email_html(html: str) -> str:
    """
    Remove all HTML tags from the input email content and return plain text.

    Args:
        html (str): Raw HTML content from email.

    Returns:
        str: Cleaned plain-text version with line breaks preserved.
    """
    return BeautifulSoup(html, 'html.parser').get_text(separator='\n', strip=True)


def parse_item_details(description: str) -> tuple[str, str, str]:
    """
    Extract structured attributes (base description, color, size) from a product description string.

    Supports multiple formats:
    1. Format: "Product Name. Color, Size"
    2. Multiline: "Product Name\nColor: xyz\nSize: abc"

    Args:
        description (str): Raw product description string from extracted item.

    Returns:
        tuple: (base_desc, color, size)
    """
    if not description:
        return "", "", ""

    # Format 1: "Product Name. Color, Size"
    match = re.match(r"^(.*?)\.\s*([^,]+),\s*(.+)$", description)
    if match:
        base = match.group(1).strip()
        color = match.group(2).strip()
        size = match.group(3).strip()
        return base, color, size

    # Format 2: Multiline with "Color: xyz", "Size: abc"
    base = description.split("\n")[0].strip()
    color_match = re.search(r"Color:\s*(.+)", description, re.IGNORECASE)
    size_match = re.search(r"Size:\s*(.+)", description, re.IGNORECASE)
    color = color_match.group(1).strip() if color_match else ""
    size = size_match.group(1).strip() if size_match else ""

    return base, color, size

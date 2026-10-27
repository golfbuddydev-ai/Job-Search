"""Shared helper used across all scripts that call the Claude API."""


def extract_text(response):
    """Return the concatenated text content from a Claude API response,
    safely skipping any non-text blocks (e.g. extended thinking blocks,
    which some responses include before the actual text)."""
    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()

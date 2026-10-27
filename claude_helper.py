"""Shared helpers used by every script that calls the Claude API."""

import json
import re

import config


def extract_text(response):
    """Return the text of a Claude API response, skipping any non-text
    blocks (e.g. thinking blocks, which some responses include first)."""
    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _parse_json(raw):
    """Parse JSON from Claude's reply, tolerating code fences, a sentence
    before or after the JSON, and stray line breaks inside strings."""
    text = raw.replace("```json", "").replace("```", "").strip()
    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    if starts:
        start = min(starts)
        end = max(text.rfind("]"), text.rfind("}"))
        if end > start:
            text = text[start:end + 1]
    return json.loads(text, strict=False)


def ask_json(client, system, user, max_tokens=4000):
    """Ask Claude for JSON and return it parsed. If the reply is cut off or
    can't be read, tries once more with double the room before giving up
    (raising an error the caller can catch and log)."""
    last_error = None
    for attempt_tokens in (max_tokens, max_tokens * 2):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=attempt_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        raw = extract_text(response)
        if getattr(response, "stop_reason", None) == "max_tokens":
            last_error = ValueError("reply was cut off before it finished")
            continue
        try:
            return _parse_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            # strip anything odd and try the stricter cleanup once more
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", raw)
            try:
                return _parse_json(cleaned)
            except (json.JSONDecodeError, ValueError) as e2:
                last_error = e2
    raise last_error

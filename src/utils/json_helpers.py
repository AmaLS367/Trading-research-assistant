from __future__ import annotations

import json


def extract_json_from_text(text: str) -> str | None:
    if not text:
        return None

    fenced = _extract_json_fence_block(text)
    if fenced is not None:
        extracted = _extract_first_json_object(fenced)
        if extracted is not None:
            return extracted

    return _extract_first_json_object(text)


def try_parse_json(text: str) -> dict[str, object] | None:
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if isinstance(parsed, dict):
        return parsed

    return None


def _extract_json_fence_block(text: str) -> str | None:
    lower = text.lower()
    fence_start = lower.find("```json")
    if fence_start == -1:
        return None

    content_start = lower.find("\n", fence_start)
    if content_start == -1:
        return None

    fence_end = lower.find("```", content_start + 1)
    if fence_end == -1:
        return None

    return text[content_start + 1 : fence_end].strip()


def _extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
            continue

        if ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1].strip()
            if depth < 0:
                return None

    return None

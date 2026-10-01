"""The custom_id contract between the renderer and the router.

A component's custom_id must self-describe: it carries the semantic
payload so the interaction handler needs no per-flow state. Encoded
compact JSON in base64url under a versioned prefix.

Discord caps custom_id at 100 characters; `encode` enforces that.
"""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any

from pydantic import BaseModel

PREFIX = "db1|"


class ClickPayload(BaseModel):
    """What one click means. `action` is reserved for direct-dispatch ops."""

    value: str
    action: dict[str, Any] | None = None


def encode(value: str, action: dict[str, Any] | None = None) -> str:
    """Build a custom_id for a button or select option."""
    body = json.dumps(
        {"v": value, "a": action}, separators=(",", ":"), ensure_ascii=False
    )
    encoded = base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")
    custom_id = PREFIX + encoded
    if len(custom_id) > 100:
        raise ValueError(
            f"payload too long ({len(custom_id)} > 100 chars): shorten value/action"
        )
    return custom_id


def decode(custom_id: str) -> ClickPayload:
    """Parse a custom_id back into a ClickPayload."""
    if not custom_id.startswith(PREFIX):
        raise ValueError(f"not a discblock custom_id: {custom_id!r}")
    encoded = custom_id[len(PREFIX) :]
    try:
        body = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        data = json.loads(body)
    except (binascii.Error, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed payload: {custom_id!r}") from exc
    if not isinstance(data, dict) or "v" not in data:
        raise ValueError(f"payload missing 'v': {custom_id!r}")
    return ClickPayload(value=data["v"], action=data.get("a"))

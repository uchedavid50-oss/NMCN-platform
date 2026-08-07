import json
from typing import Optional

from pydantic import field_validator


class WhyOthersWrongMixin:
    """Shared parsing for the why_others_wrong column, which is stored as a
    JSON-encoded string (this codebase has no JSON/JSONB column elsewhere)
    but should come out of the API as a dict."""

    why_others_wrong: Optional[dict] = None

    @field_validator("why_others_wrong", mode="before")
    @classmethod
    def _parse_why_others_wrong(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v

"""Value object representing a single cached payload."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """An immutable snapshot stored by a :class:`CacheRepository`.

    ``payload`` is a plain JSON-serializable dict rather than a typed domain
    model so the cache layer stays provider-agnostic: it does not need to
    know about ``Profile`` or ``Stats`` to store and retrieve them.
    """

    key: str
    payload: dict[str, Any]
    updated_at: datetime

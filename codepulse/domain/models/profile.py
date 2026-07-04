"""A user's public profile on a coding platform."""

from __future__ import annotations

from pydantic import BaseModel


class Profile(BaseModel):
    """Provider-agnostic public profile information."""

    username: str
    real_name: str | None = None
    avatar_url: str | None = None
    ranking: int | None = None
    country: str | None = None

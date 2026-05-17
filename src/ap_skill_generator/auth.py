from __future__ import annotations

from fastapi import Header, HTTPException

from .config import Settings


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def verify_api_key(
    *,
    x_api_key: str | None,
    authorization: str | None,
    settings: Settings,
) -> None:
    expected = settings.api_key.strip()
    if not expected:
        return

    provided = (x_api_key or "").strip() or (_extract_bearer_token(authorization) or "")
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> None:
    verify_api_key(x_api_key=x_api_key, authorization=authorization, settings=Settings())

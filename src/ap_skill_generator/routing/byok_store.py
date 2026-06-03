from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ByokCredentials:
    api_key: str
    model: str | None = None


@dataclass
class _StoredEntry:
    creds: ByokCredentials
    expires_at: float


class ByokCredentialStore:
    def __init__(self, *, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, _StoredEntry] = {}

    def set(self, session_id: str, *, api_key: str, model: str | None = None) -> None:
        key = api_key.strip()
        self._entries[session_id] = _StoredEntry(
            creds=ByokCredentials(api_key=key, model=(model or "").strip() or None),
            expires_at=time.monotonic() + self._ttl_seconds,
        )

    def get(self, session_id: str) -> ByokCredentials | None:
        entry = self._entries.get(session_id)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._entries[session_id]
            return None
        return entry.creds

    def delete(self, session_id: str) -> bool:
        return self._entries.pop(session_id, None) is not None

    def has(self, session_id: str) -> bool:
        return self.get(session_id) is not None

from __future__ import annotations

from .config import Settings

_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset cached settings (for tests)."""
    global _settings
    _settings = None

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_local_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_local_env_file()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ap_skill_generator.db")
    api_key: str = os.getenv("API_KEY", "")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    rate_limit_generate: int = int(os.getenv("RATE_LIMIT_GENERATE", "10"))
    rate_limit_items: int = int(os.getenv("RATE_LIMIT_ITEMS", "60"))
    rate_limit_generate_sample: int = int(os.getenv("RATE_LIMIT_GENERATE_SAMPLE", "3"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
    apforge_core_provider: str = os.getenv("APFORGE_CORE_PROVIDER", "openai_compatible")
    apforge_core_model: str = os.getenv("APFORGE_CORE_MODEL", "gpt-4o-mini")
    apforge_core_api_key: str = os.getenv("APFORGE_CORE_API_KEY", "")
    apforge_core_base_url: str = os.getenv(
        "APFORGE_CORE_BASE_URL",
        "https://api.openai.com/v1",
    )
    apforge_env: str = os.getenv("APFORGE_ENV", "development")
    free_sample_size: int = int(os.getenv("FREE_SAMPLE_SIZE", "5"))
    free_sample_min_usable: int = int(os.getenv("FREE_SAMPLE_MIN_USABLE", "3"))
    free_max_repair: int = int(os.getenv("FREE_MAX_REPAIR", "1"))
    free_allow_policy_fallback: bool = _env_bool("FREE_ALLOW_POLICY_FALLBACK", False)
    free_allow_soft_retry: bool = _env_bool("FREE_ALLOW_SOFT_RETRY", False)
    byok_max_repair: int = int(os.getenv("BYOK_MAX_REPAIR", "3"))
    byok_credential_ttl_seconds: int = int(os.getenv("BYOK_CREDENTIAL_TTL_SECONDS", "86400"))
    byok_default_base_url: str = os.getenv("BYOK_DEFAULT_BASE_URL", "https://api.openai.com/v1")
    free_sample_pending_stale_minutes: int = int(os.getenv("FREE_SAMPLE_PENDING_STALE_MINUTES", "15"))

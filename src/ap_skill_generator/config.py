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
    cors_origins: str = os.getenv("CORS_ORIGINS", "")

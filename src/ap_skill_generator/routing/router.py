from __future__ import annotations

from dataclasses import replace

from fastapi import HTTPException

from ..config import Settings
from ..providers import OpenAICompatibleProvider
from .byok_store import ByokCredentialStore, ByokCredentials
from .quota import FreeSampleQuota
from .types import GenerationLimits, ResolvedRoute, UserMode


class UnsupportedProviderError(ValueError):
    pass


def build_provider(provider_kind: str, settings_slice: Settings) -> OpenAICompatibleProvider:
    if provider_kind != "openai_compatible":
        raise UnsupportedProviderError(provider_kind)
    return OpenAICompatibleProvider(settings_slice)


class ModelRouter:
    def __init__(
        self,
        *,
        settings: Settings,
        byok_store: ByokCredentialStore,
        quota: FreeSampleQuota,
    ) -> None:
        self.settings = settings
        self.byok_store = byok_store
        self.quota = quota

    def core_settings(self) -> Settings:
        key = self.settings.apforge_core_api_key.strip()
        if not key and self.settings.apforge_env == "development":
            key = self.settings.openai_api_key.strip()
        base_url = self.settings.apforge_core_base_url.strip() or self.settings.openai_base_url
        model = self.settings.apforge_core_model.strip() or self.settings.openai_model
        return replace(
            self.settings,
            openai_api_key=key,
            openai_base_url=base_url,
            openai_model=model,
        )

    def core_configured(self) -> bool:
        core = self.core_settings()
        return bool(core.openai_api_key.strip())

    def resolve_for_generate(self, session_id: str) -> ResolvedRoute:
        creds = self.byok_store.get(session_id)
        if creds is None:
            raise HTTPException(
                status_code=403,
                detail="Free mode uses POST /generate/sample. Connect your API key for single-question generation.",
            )
        return self._byok_route(creds)

    def resolve_for_sample(self, session_id: str, *, ip: str) -> tuple[ResolvedRoute, str]:
        claim = self.quota.begin_sample(session_id, ip_hash=self._hash_ip(ip))
        core = self.core_settings()
        if not core.openai_api_key.strip():
            self.quota.mark_failed(claim.sample_id)
            raise HTTPException(
                status_code=503,
                detail="APForge Core is not configured. Set APFORGE_CORE_API_KEY.",
            )
        limits = GenerationLimits(
            max_repair=self.settings.free_max_repair,
            allow_policy_fallback=self.settings.free_allow_policy_fallback,
            allow_soft_retry=self.settings.free_allow_soft_retry,
        )
        route = ResolvedRoute(
            mode="free",
            provider_kind=self.settings.apforge_core_provider,
            provider_settings=core,
            limits=limits,
        )
        return route, claim.sample_id

    def finish_sample(self, sample_id: str, *, usable_count: int) -> str:
        if usable_count >= self.settings.free_sample_min_usable:
            self.quota.mark_consumed(sample_id)
            return "consumed"
        self.quota.mark_failed(sample_id)
        return "failed"

    def free_sample_available(self, session_id: str) -> bool:
        return self.quota.can_start_sample(session_id)

    def _byok_route(self, creds: ByokCredentials) -> ResolvedRoute:
        provider_settings = replace(
            self.settings,
            openai_api_key=creds.api_key,
            openai_base_url=self.settings.byok_default_base_url,
            openai_model=creds.model or self.settings.openai_model,
        )
        limits = GenerationLimits(
            max_repair=self.settings.byok_max_repair,
            allow_policy_fallback=True,
            allow_soft_retry=True,
        )
        return ResolvedRoute(
            mode="byok",
            provider_kind="openai_compatible",
            provider_settings=provider_settings,
            limits=limits,
        )

    @staticmethod
    def _hash_ip(ip: str) -> str:
        import hashlib

        normalized = ip.strip() or "unknown"
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

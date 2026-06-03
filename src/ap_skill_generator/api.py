from __future__ import annotations

import re
import uuid
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from .auth import require_api_key
from .dependencies import get_settings
from .engine import APGenerationEngine
from .rate_limit import RateLimiter, client_ip
from .routing import ByokCredentialStore, FreeSampleQuota, ModelRouter
from .schema import GenerateRequest
from .skills import SkillValidationError

_settings = get_settings()
_byok_store = ByokCredentialStore(ttl_seconds=_settings.byok_credential_ttl_seconds)
_quota = FreeSampleQuota(_settings)
_router = ModelRouter(settings=_settings, byok_store=_byok_store, quota=_quota)
_engine = APGenerationEngine(settings=_settings)
_rate_limiter = RateLimiter(
    limits={
        "generate": (_settings.rate_limit_generate, 60),
        "generate_sample": (_settings.rate_limit_generate_sample, 60),
        "items": (_settings.rate_limit_items, 60),
    }
)

app = FastAPI(title="AP Skill Generator API", version="0.3.0")

if _settings.cors_origins.strip():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _settings.cors_origins.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )

_SESSION_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def get_engine() -> APGenerationEngine:
    return _engine


def get_model_router() -> ModelRouter:
    return _router


def get_byok_store() -> ByokCredentialStore:
    return _byok_store


def resolve_session_id(
    x_apforge_session: str | None = Header(default=None, alias="X-APForge-Session"),
) -> str:
    raw = (x_apforge_session or "").strip()
    if raw and _SESSION_RE.match(raw):
        return raw
    return str(uuid.uuid4())


class HarnessInfo(BaseModel):
    mode: str
    status: str
    policy_status: str
    used_fallback: bool
    failure_reason_code: str
    reasons: list[str]
    attempt_count_by_skill: dict[str, int]
    repair_classes: list[str]


class GenerateResponse(BaseModel):
    run_id: str
    request_id: str
    item: dict
    metrics: dict
    harness: HarnessInfo


class SampleGenerateResponse(BaseModel):
    sample_id: str
    items: list[dict[str, Any]]
    validation_report: dict[str, Any]
    claim_status: str
    usable_count: int


class ByokCredentialsRequest(BaseModel):
    api_key: str = Field(min_length=1)
    model: str | None = None


ItemsSort = Literal["newest", "oldest", "quality_desc", "quality_asc"]


class ItemRowResponse(BaseModel):
    run_id: str
    created_at: str
    subject: str
    skill: str
    difficulty: int
    type: str
    final_status: str
    status: str
    failure_reason_code: str | None = None
    quality_score: float | None
    question: str
    choices: list
    answer: str
    explanation: str
    metadata: dict
    visual: dict | None = None


class ItemsListResponse(BaseModel):
    items: list[ItemRowResponse]
    total: int
    page: int
    page_size: int


@app.get("/config")
def public_config(
    session_id: str = Depends(resolve_session_id),
    router: ModelRouter = Depends(get_model_router),
):
    return {
        "api_auth_required": bool(_settings.api_key.strip()),
        "llm_configured": bool(_settings.openai_api_key.strip()),
        "core_configured": router.core_configured(),
        "free_sample_available": router.free_sample_available(session_id),
        "byok_connected": _byok_store.has(session_id),
        "free_max_repair": _settings.free_max_repair,
        "byok_max_repair": _settings.byok_max_repair,
        "free_sample_size": _settings.free_sample_size,
        "free_sample_min_usable": _settings.free_sample_min_usable,
    }


@app.post("/byok/credentials", status_code=204)
def store_byok_credentials(
    payload: ByokCredentialsRequest,
    session_id: str = Depends(resolve_session_id),
    _: None = Depends(require_api_key),
    store: ByokCredentialStore = Depends(get_byok_store),
):
    if not payload.api_key.strip():
        raise HTTPException(status_code=422, detail="api_key is required")
    store.set(session_id, api_key=payload.api_key, model=payload.model)
    return Response(status_code=204)


@app.delete("/byok/credentials", status_code=204)
def delete_byok_credentials(
    session_id: str = Depends(resolve_session_id),
    _: None = Depends(require_api_key),
    store: ByokCredentialStore = Depends(get_byok_store),
):
    store.delete(session_id)
    return Response(status_code=204)


@app.post("/generate", response_model=GenerateResponse)
def generate(
    payload: GenerateRequest,
    http_request: Request,
    _: None = Depends(require_api_key),
    engine: APGenerationEngine = Depends(get_engine),
    router: ModelRouter = Depends(get_model_router),
    session_id: str = Depends(resolve_session_id),
):
    _rate_limiter.check(client_key=client_ip(http_request), route_key="generate")
    route = router.resolve_for_generate(session_id)
    try:
        return engine.generate(payload, route=route)
    except SkillValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/generate/sample", response_model=SampleGenerateResponse)
def generate_sample(
    payload: GenerateRequest,
    http_request: Request,
    _: None = Depends(require_api_key),
    engine: APGenerationEngine = Depends(get_engine),
    router: ModelRouter = Depends(get_model_router),
    session_id: str = Depends(resolve_session_id),
):
    _rate_limiter.check(client_key=client_ip(http_request), route_key="generate_sample")
    ip = client_ip(http_request)
    route, sample_id = router.resolve_for_sample(session_id, ip=ip)
    try:
        batch = engine.generate_sample(
            payload,
            route=route,
            sample_id=sample_id,
            sample_size=_settings.free_sample_size,
        )
        claim_status = router.finish_sample(sample_id, usable_count=batch["usable_count"])
        return SampleGenerateResponse(
            sample_id=batch["sample_id"],
            items=batch["items"],
            validation_report=batch["validation_report"],
            claim_status=claim_status,
            usable_count=batch["usable_count"],
        )
    except HTTPException:
        raise
    except SkillValidationError as exc:
        router.finish_sample(sample_id, usable_count=0)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValidationError as exc:
        router.finish_sample(sample_id, usable_count=0)
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except Exception as exc:  # noqa: BLE001
        router.finish_sample(sample_id, usable_count=0)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/items", response_model=ItemsListResponse)
def items(
    http_request: Request,
    run_id: str | None = Query(default=None),
    sample_id: str | None = Query(default=None),
    subject: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    difficulty: int | None = Query(default=None),
    type: str | None = Query(default=None, alias="type"),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    quality_min: float | None = Query(default=None),
    quality_max: float | None = Query(default=None),
    has_quality: bool | None = Query(default=None),
    sort: ItemsSort = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    _: None = Depends(require_api_key),
    engine: APGenerationEngine = Depends(get_engine),
):
    _rate_limiter.check(client_key=client_ip(http_request), route_key="items")
    search_q = q.strip() if q and q.strip() else None
    return engine.query_items(
        run_id=run_id,
        sample_id=sample_id,
        subject=subject,
        skill=skill,
        difficulty=difficulty,
        item_type=type,
        status=status,
        q=search_q,
        quality_min=quality_min,
        quality_max=quality_max,
        has_quality=has_quality,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@app.delete("/items/{run_id}", status_code=204)
def delete_item(
    run_id: str,
    http_request: Request,
    _: None = Depends(require_api_key),
    engine: APGenerationEngine = Depends(get_engine),
):
    _rate_limiter.check(client_key=client_ip(http_request), route_key="items")
    if not engine.delete_item(run_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return Response(status_code=204)


@app.get("/stats")
def stats(
    http_request: Request,
    _: None = Depends(require_api_key),
    engine: APGenerationEngine = Depends(get_engine),
):
    _rate_limiter.check(client_key=client_ip(http_request), route_key="items")
    return engine.get_dashboard_stats()


@app.get("/health")
def health():
    return {"status": "ok"}

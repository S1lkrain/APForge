from __future__ import annotations

from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from .auth import require_api_key
from .dependencies import get_settings
from .engine import APGenerationEngine
from .rate_limit import RateLimiter, client_ip
from .schema import GenerateRequest
from .skills import SkillValidationError

_settings = get_settings()
_engine = APGenerationEngine(settings=_settings)
_rate_limiter = RateLimiter(
    limits={
        "generate": (_settings.rate_limit_generate, 60),
        "items": (_settings.rate_limit_items, 60),
    }
)

app = FastAPI(title="AP Skill Generator API", version="0.2.0")

if _settings.cors_origins.strip():
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _settings.cors_origins.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_engine() -> APGenerationEngine:
    return _engine


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


class ItemsListResponse(BaseModel):
    items: list[ItemRowResponse]
    total: int
    page: int
    page_size: int


@app.get("/config")
def public_config():
    return {
        "api_auth_required": bool(_settings.api_key.strip()),
        "llm_configured": bool(_settings.openai_api_key.strip()),
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(
    payload: GenerateRequest,
    http_request: Request,
    _: None = Depends(require_api_key),
    engine: APGenerationEngine = Depends(get_engine),
    x_llm_api_key: str | None = Header(default=None, alias="X-LLM-API-Key"),
):
    _rate_limiter.check(client_key=client_ip(http_request), route_key="generate")
    try:
        return engine.generate(payload, llm_api_key=x_llm_api_key)
    except SkillValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/items", response_model=ItemsListResponse)
def items(
    http_request: Request,
    run_id: str | None = Query(default=None),
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

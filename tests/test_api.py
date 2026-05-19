from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ap_skill_generator.api import _rate_limiter, app, get_engine
from ap_skill_generator.auth import verify_api_key
from ap_skill_generator.config import Settings
from ap_skill_generator.dependencies import get_settings, reset_settings
from ap_skill_generator.engine import APGenerationEngine
from ap_skill_generator.providers import OFFLINE_MODEL_ID


@pytest.fixture
def api_client():
    _rate_limiter.reset()
    reset_settings()
    settings = Settings(database_url="sqlite:///:memory:", openai_api_key="", api_key="")
    engine = APGenerationEngine(settings=settings)
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_settings] = lambda: settings
    yield TestClient(app)
    app.dependency_overrides.clear()
    reset_settings()
    _rate_limiter.reset()


@pytest.fixture
def authed_client():
    _rate_limiter.reset()
    reset_settings()
    settings = Settings(
        database_url="sqlite:///:memory:",
        openai_api_key="",
        api_key="secret-test-key",
    )
    engine = APGenerationEngine(settings=settings)
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app)
    client.headers.update({"X-API-Key": "secret-test-key"})
    yield client
    app.dependency_overrides.clear()
    reset_settings()
    _rate_limiter.reset()


def test_generate_returns_harness_fields(api_client):
    response = api_client.post(
        "/generate",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 2,
            "type": "mcq",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "harness" in body
    assert body["harness"]["status"] in {"accepted", "accepted_with_warning", "fallback"}
    assert "policy_status" in body["harness"]
    assert body["item"]["metadata"]["model_id"] == OFFLINE_MODEL_ID


def test_verify_api_key_enforced_when_configured():
    settings = Settings(api_key="secret-test-key")
    with pytest.raises(HTTPException) as exc:
        verify_api_key(x_api_key=None, authorization=None, settings=settings)
    assert exc.value.status_code == 401

    verify_api_key(x_api_key="secret-test-key", authorization=None, settings=settings)


def test_verify_api_key_skipped_when_unset():
    settings = Settings(api_key="")
    verify_api_key(x_api_key=None, authorization=None, settings=settings)


def test_health_endpoint(api_client):
    assert api_client.get("/health").json() == {"status": "ok"}


def test_config_endpoint(api_client):
    body = api_client.get("/config").json()
    assert set(body) == {"api_auth_required", "llm_configured"}
    assert isinstance(body["api_auth_required"], bool)
    assert isinstance(body["llm_configured"], bool)


def test_items_include_quality_and_status(api_client):
    api_client.post(
        "/generate",
        json={
            "subject": "ap_precalculus",
            "skill": "limits",
            "difficulty": 3,
            "type": "mcq",
        },
    )
    body = api_client.get("/items").json()
    assert body["total"] >= 1
    assert body["page"] == 1
    assert "page_size" in body
    row = body["items"][0]
    assert "quality_score" in row
    assert row["quality_score"] is not None
    assert row["status"] in {"Success", "Warn", "Rejected"}


def _generate(api_client, *, skill: str, difficulty: int = 2, item_type: str = "mcq"):
    return api_client.post(
        "/generate",
        json={
            "subject": "ap_precalculus",
            "skill": skill,
            "difficulty": difficulty,
            "type": item_type,
        },
    )


def test_items_pagination(api_client):
    for skill in ("limits", "linear-functions", "polynomials"):
        _generate(api_client, skill=skill)

    page1 = api_client.get("/items", params={"page": 1, "page_size": 2}).json()
    assert page1["total"] >= 3
    assert len(page1["items"]) == 2
    assert page1["page"] == 1
    assert page1["page_size"] == 2

    page2 = api_client.get("/items", params={"page": 2, "page_size": 2}).json()
    assert len(page2["items"]) >= 1
    assert page1["items"][0]["run_id"] != page2["items"][0]["run_id"]


def test_items_search(api_client):
    _generate(api_client, skill="limits")
    _generate(api_client, skill="trigonometry")

    limits = api_client.get("/items", params={"q": "limits"}).json()
    assert limits["total"] >= 1
    assert all("limit" in row["skill"].lower() or "limit" in row["question"].lower() for row in limits["items"])

    mcq = api_client.get("/items", params={"q": "mcq", "type": "mcq"}).json()
    assert mcq["total"] >= 1


def test_items_whitespace_search_matches_all(api_client):
    _generate(api_client, skill="limits")
    _generate(api_client, skill="trigonometry")

    body = api_client.get("/items", params={"q": "   "}).json()
    assert body["total"] >= 2


def test_items_filters_and_sort(api_client):
    _generate(api_client, skill="limits", difficulty=2)
    _generate(api_client, skill="limits", difficulty=4)

    filtered = api_client.get(
        "/items",
        params={"skill": "limits", "difficulty": 2},
    ).json()
    assert filtered["total"] >= 1
    assert all(row["skill"] == "limits" and row["difficulty"] == 2 for row in filtered["items"])

    oldest = api_client.get("/items", params={"sort": "oldest", "page_size": 50}).json()
    dates = [row["created_at"] for row in oldest["items"]]
    assert dates == sorted(dates)


def test_items_subject_filter(api_client):
    _generate(api_client, skill="limits")
    body = api_client.get("/items", params={"subject": "ap_precalculus"}).json()
    assert body["total"] >= 1
    assert all(row["subject"] == "ap_precalculus" for row in body["items"])


def test_items_status_filter(api_client):
    _generate(api_client, skill="limits")
    all_body = api_client.get("/items", params={"page_size": 50}).json()
    assert all_body["total"] >= 1
    expected_status = all_body["items"][0]["status"]
    status_param = {
        "Success": "success",
        "Warn": "warn",
        "Rejected": "rejected",
    }[expected_status]
    body = api_client.get("/items", params={"status": status_param}).json()
    assert body["total"] >= 1
    assert all(row["status"] == expected_status for row in body["items"])


def test_items_quality_filters(api_client):
    _generate(api_client, skill="limits")
    body = api_client.get("/items", params={"quality_min": 0, "page_size": 50}).json()
    assert body["total"] >= 1
    assert all(row["quality_score"] is not None and row["quality_score"] >= 0 for row in body["items"])

    none_body = api_client.get("/items", params={"has_quality": False}).json()
    assert all(row["quality_score"] is None for row in none_body["items"])


def test_items_quality_sort(api_client):
    for skill in ("limits", "linear-functions", "polynomials"):
        _generate(api_client, skill=skill)

    desc = api_client.get("/items", params={"sort": "quality_desc", "page_size": 50}).json()
    scores = [row["quality_score"] for row in desc["items"] if row["quality_score"] is not None]
    assert scores == sorted(scores, reverse=True)

    asc = api_client.get("/items", params={"sort": "quality_asc", "page_size": 50}).json()
    asc_scores = [row["quality_score"] for row in asc["items"] if row["quality_score"] is not None]
    assert asc_scores == sorted(asc_scores)


def test_items_invalid_sort_returns_422(api_client):
    response = api_client.get("/items", params={"sort": "invalid"})
    assert response.status_code == 422


def test_items_page_beyond_last(api_client):
    _generate(api_client, skill="limits")
    body = api_client.get("/items", params={"page": 99, "page_size": 10}).json()
    assert body["items"] == []
    assert body["page"] == 99


def test_items_page_size_cap(api_client):
    response = api_client.get("/items", params={"page_size": 100})
    assert response.status_code == 422


def test_items_page_size_max(api_client):
    for _ in range(3):
        _generate(api_client, skill="limits")
    body = api_client.get("/items", params={"page_size": 50}).json()
    assert body["page_size"] == 50


def test_delete_item(api_client):
    response = _generate(api_client, skill="limits")
    run_id = response.json()["run_id"]

    delete_response = api_client.delete(f"/items/{run_id}")
    assert delete_response.status_code == 204

    missing = api_client.get("/items", params={"run_id": run_id}).json()
    assert missing["total"] == 0

    not_found = api_client.delete(f"/items/{run_id}")
    assert not_found.status_code == 404


def test_items_requires_api_key_when_configured(authed_client):
    body = authed_client.get("/items").json()
    assert body["total"] >= 0


def test_items_rejects_missing_api_key_when_configured():
    _rate_limiter.reset()
    reset_settings()
    settings = Settings(
        database_url="sqlite:///:memory:",
        openai_api_key="",
        api_key="secret-test-key",
    )
    engine = APGenerationEngine(settings=settings)
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app)
    try:
        response = client.get("/items")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
        reset_settings()
        _rate_limiter.reset()


def test_delete_requires_api_key_when_configured(authed_client):
    response = _generate(authed_client, skill="limits")
    run_id = response.json()["run_id"]
    assert authed_client.delete(f"/items/{run_id}").status_code == 204


def test_rate_limit_returns_429(api_client):
    original = _rate_limiter.limits["items"]
    _rate_limiter.limits["items"] = (1, 60)
    _rate_limiter.reset()
    try:
        assert api_client.get("/items").status_code == 200
        assert api_client.get("/items").status_code == 429
    finally:
        _rate_limiter.limits["items"] = original
        _rate_limiter.reset()


def test_stats_endpoint(api_client):
    api_client.post(
        "/generate",
        json={
            "subject": "ap_precalculus",
            "skill": "linear-functions",
            "difficulty": 2,
            "type": "frq",
        },
    )
    stats = api_client.get("/stats").json()
    assert stats["total_generated"] >= 1
    assert stats["total_runs"] >= 1
    assert 0.0 <= stats["success_rate"] <= 1.0
    assert "avg_quality_score" in stats
    assert "week_delta" in stats
    assert "total_generated" in stats["week_delta"]

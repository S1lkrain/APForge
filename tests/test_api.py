from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ap_skill_generator.api import app, get_engine
from ap_skill_generator.auth import verify_api_key
from ap_skill_generator.config import Settings
from ap_skill_generator.engine import APGenerationEngine
from ap_skill_generator.providers import OFFLINE_MODEL_ID


@pytest.fixture
def api_client():
    settings = Settings(database_url="sqlite:///:memory:", openai_api_key="", api_key="")
    engine = APGenerationEngine(settings=settings)
    app.dependency_overrides[get_engine] = lambda: engine
    yield TestClient(app)
    app.dependency_overrides.clear()


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
    items = api_client.get("/items").json()["items"]
    assert len(items) >= 1
    row = items[0]
    assert "quality_score" in row
    assert row["quality_score"] is not None
    assert row["status"] in {"Success", "Warn", "Rejected"}


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

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

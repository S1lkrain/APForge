from __future__ import annotations

import pytest

from ap_skill_generator.config import Settings


@pytest.fixture
def memory_settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        openai_api_key="",
        api_key="",
    )


@pytest.fixture
def engine(memory_settings):
    from ap_skill_generator.engine import APGenerationEngine

    eng = APGenerationEngine(settings=memory_settings)
    yield eng

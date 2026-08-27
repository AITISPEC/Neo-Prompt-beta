import pytest

from pro.model_manager import ModelManager


@pytest.fixture
def sample_preset():
    return {
        "id": "test-preset",
        "name": "Test",
        "file": "test.preset.json",
        "system_prompt": "You are a helpful assistant.",
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 4096,
    }


@pytest.fixture
def manager():
    return ModelManager()

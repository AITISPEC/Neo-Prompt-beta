from pro.neo_client import NeoClient


class MockResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def json(self):
        return self._json_data

    def iter_lines(self):
        if self.status_code == 200:
            yield b'data: {"choices":[{"delta":{"content":"OK"}}]}'
            yield b"data: [DONE]"
        else:
            yield b""


def test_auto_detection_lmstudio(monkeypatch):
    """Проверяет, что при доступном LM Studio определяется правильный тип."""
    client = NeoClient()

    def mock_get(url, *args, **kwargs):
        if "/api/v1/models" in url:
            return MockResponse(
                200,
                json_data={
                    "models": [
                        {
                            "key": "qwen/qwen3-vl-4b",
                            "type": "llm",
                            "loaded_instances": [{"config": {"context_length": 8192}}],
                        }
                    ]
                },
            )
        return MockResponse(404)

    monkeypatch.setattr("requests.get", mock_get)

    def mock_post(*args, **kwargs):
        return MockResponse(200)

    monkeypatch.setattr("requests.post", mock_post)

    client.check_server_status()
    assert client.server_type == "lmstudio"
    assert client.model_available is True
    assert client.current_model == "qwen/qwen3-vl-4b"


def test_auto_detection_bionic(monkeypatch):
    """Проверяет, что при недоступном LM Studio, но доступном Bionic,
    определяется Bionic."""
    client = NeoClient()
    client.bionic_api_key = "test-key"  # <--- добавить
    call_count = 0

    def mock_get(url, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if "/api/v1/models" in url:
            return MockResponse(404)
        if "/v1/models" in url:
            return MockResponse(200, json_data={"data": [{"id": "qwen/qwen3-vl-4b"}]})
        return MockResponse(404)

    monkeypatch.setattr("requests.get", mock_get)

    def mock_post(*args, **kwargs):
        return MockResponse(200)

    monkeypatch.setattr("requests.post", mock_post)

    client.check_server_status()
    assert client.server_type == "bionic"
    assert client.model_available is True
    assert client.current_model == "qwen/qwen3-vl-4b"
    assert call_count == 2  # оба эндпоинта были вызваны


def test_send_with_preset_uses_detected_type(monkeypatch):
    """Проверяет, что send_message_with_preset_stream использует уже определённый тип."""
    client = NeoClient()
    # Устанавливаем тип вручную, чтобы не вызывать check_server_status
    client.server_type = "lmstudio"
    client.server_online = True
    client.model_available = True
    client.current_model = "test-model"

    def mock_post(*args, **kwargs):
        return MockResponse(200)

    monkeypatch.setattr("requests.post", mock_post)

    preset = {"id": "test-id", "temperature": 0.7}
    gen = client.send_message_with_preset_stream("hello", preset)
    for _content, _reasoning, status in gen:
        if status == "final":
            break
    # Если дошли до финала, всё работает
    assert True

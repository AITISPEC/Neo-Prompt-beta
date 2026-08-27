import json

from pro.presets import load_presets_from_files


def test_load_presets(mocker):
    mock_data = {
        "identifier": "my-preset",
        "name": "My Preset",
        "systemPrompt": "Be concise.",
        "temperature": 0.5,
        "topP": 0.8,
        "maxTokens": 2048,
    }
    mocker.patch("glob.glob", return_value=["/fake/path.preset.json"])
    mocker.patch("builtins.open", mocker.mock_open(read_data=json.dumps(mock_data)))

    presets = load_presets_from_files()
    assert len(presets) == 1
    p = presets[0]
    assert p["id"] == "my-preset"
    assert p["name"] == "My Preset"
    # Проверяем, что поля из пресета НЕ читаются (кроме id и name)
    assert "system_prompt" not in p
    assert "temperature" not in p
    assert "top_p" not in p
    assert "max_tokens" not in p

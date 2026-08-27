def test_select_preset(manager, sample_preset):
    manager.available_presets = [sample_preset]
    status = manager.select_preset(
        0, f"{sample_preset['name']} ({sample_preset['file']})"
    )
    assert status.startswith("✅")
    assert manager.current_presets[0] == "test-preset"


def test_get_preset_by_index(manager, sample_preset):
    manager.available_presets = [sample_preset]
    assert manager.get_preset_by_index(0) == sample_preset
    assert manager.get_preset_by_index(1) is None

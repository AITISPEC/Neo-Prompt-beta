import glob
import json
import os
from pathlib import Path

PRESETS_PATH = os.path.expanduser("~/.lmstudio/config-presets/*.preset.json")


def load_presets_from_files():
    """Загружает идентификаторы пресетов из файлов"""
    presets = []
    preset_files = glob.glob(PRESETS_PATH)

    for file_path in preset_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            preset_id = data.get("identifier", Path(file_path).stem)
            preset_name = data.get("name", Path(file_path).stem)

            presets.append(
                {
                    "id": preset_id,
                    "name": preset_name,
                    "file": os.path.basename(file_path),
                }
            )
        except OSError as e:
            print(f"Ошибка загрузки {file_path}: {e}")

    return presets

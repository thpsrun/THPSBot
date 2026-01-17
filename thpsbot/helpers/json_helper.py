import json
from pathlib import Path
from typing import Any


class JsonHelper:
    @staticmethod
    def load_json(filepath: str) -> Any:
        """Loads and returns JSON data from the specified filepath."""
        with open(Path(filepath), "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json(data: Any, filepath: str) -> None:
        """Saves JSON data to the specified filepath."""
        with open(Path(filepath), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonHelper:
    @staticmethod
    def load_json(
        filepath: str,
    ) -> Any:
        with open(Path(filepath), "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_json(
        data: Any,
        filepath: str,
    ) -> None:
        """Atomically write JSON to a file.
        Arguments:
            data (Any): The JSON-serializable object to persist.
            filepath (str): Destination path for the JSON file.

        Raises:
            TypeError: When ``data`` is not JSON-serializable (raised by
                ``json.dump`` before the destination is touched).
        """
        target = Path(filepath)
        directory = target.parent

        fd, tmp_path = tempfile.mkstemp(
            dir=directory,
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, target)
        except BaseException:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise

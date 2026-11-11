"""Small JSON-file persistence helpers with atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable


class JsonFileStore:
    """A JSON document on disk, written atomically.

    A corrupted document is moved aside to ``<name>.corrupt`` and the default
    value is returned so JARVIS keeps working instead of crashing at startup.
    """

    def __init__(self, path: str | os.PathLike[str], default_factory: Callable[[], Any] = list):
        self.path = Path(path)
        self._default_factory = default_factory

    def _default(self) -> Any:
        return self._default_factory()

    def read(self) -> Any:
        if not self.path.is_file():
            return self._default()
        try:
            raw = self.path.read_text(encoding="utf-8")
            if not raw.strip():
                return self._default()
            return json.loads(raw)
        except (OSError, json.JSONDecodeError):
            self._quarantine()
            return self._default()

    def write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        handle_fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=str(self.path.parent))
        try:
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def _quarantine(self) -> None:
        try:
            os.replace(self.path, self.path.with_suffix(self.path.suffix + ".corrupt"))
        except OSError:
            pass

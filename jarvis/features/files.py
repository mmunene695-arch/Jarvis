"""Sandboxed text-file manager.

Every path is resolved inside the caller supplied root; names containing path
separators, parent references or an absolute path are rejected.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from ..errors import NotFoundError, UnsafeInputError, ValidationError

TEXT_SUFFIXES = {".txt", ".md", ".json", ".csv", ".log", ".ini", ".yaml", ".yml"}
MAX_FILE_BYTES = 512 * 1024

_BAD_CHARS = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


@dataclass
class FileManager:
    """Reads and creates text files inside a single directory."""

    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def clean_name(self, raw: str) -> str:
        """Validate a user supplied file name and return it normalised."""
        if raw is None:
            raise ValidationError("no file name given")
        name = str(raw).strip().strip("\"'").strip()
        if not name:
            raise ValidationError("no file name given")
        if len(name) > 120:
            raise ValidationError("that file name is too long")
        if name in {".", ".."} or ".." in Path(name).parts:
            raise UnsafeInputError("file names cannot contain parent directory references")
        if Path(name).is_absolute() or name.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:", name):
            raise UnsafeInputError("file names must be relative to the Jarvis files folder")
        if _BAD_CHARS.search(name):
            raise UnsafeInputError("file names cannot contain control characters or path separators")
        if not Path(name).suffix:
            name = f"{name}.txt"
        if Path(name).suffix.lower() not in TEXT_SUFFIXES:
            raise ValidationError(
                "only text files are supported: " + ", ".join(sorted(TEXT_SUFFIXES))
            )
        return name

    def resolve(self, raw: str) -> Path:
        name = self.clean_name(raw)
        path = (self.root / name).resolve()
        if self.root != path.parent and self.root not in path.parents:
            raise UnsafeInputError("that path is outside the Jarvis files folder")
        return path

    # ------------------------------------------------------------------
    def exists(self, raw: str) -> bool:
        return self.resolve(raw).is_file()

    def create(self, raw: str, content: str = "") -> Path:
        """Create a file. Never overwrites an existing file."""
        path = self.resolve(raw)
        if path.exists():
            raise ValidationError(f"{path.name} already exists and I will not overwrite it")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content if content.endswith("\n") or not content else content + "\n")
        return path

    def read(self, raw: str, *, max_bytes: int = MAX_FILE_BYTES) -> str:
        path = self.resolve(raw)
        if not path.is_file():
            raise NotFoundError(f"I could not find {path.name} in the Jarvis files folder")
        if path.stat().st_size > max_bytes:
            raise ValidationError(f"{path.name} is larger than I am willing to read ({max_bytes} bytes)")
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ValidationError(f"I could not read {path.name}: {exc}") from exc

    def list_files(self) -> list[Path]:
        try:
            entries = [
                p
                for p in self.root.iterdir()
                if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and not p.name.startswith(".")
            ]
        except OSError:
            return []
        return sorted(entries, key=lambda p: p.name.lower())

    def search(self, query: str) -> list[Path]:
        needle = (query or "").strip().lower()
        if not needle:
            return []
        return [p for p in self.list_files() if needle in p.name.lower()]

    def describe_files(self) -> str:
        files = self.list_files()
        if not files:
            return f"The Jarvis files folder is empty ({self.root})."
        lines = [f"I have {len(files)} text file(s) in {self.root}:"]
        for path in files[:40]:
            lines.append(f"• {path.name} ({_human_size(path.stat().st_size)})")
        if len(files) > 40:
            lines.append(f"…and {len(files) - 40} more.")
        return "\n".join(lines)

    def describe_matches(self, matches: list[Path]) -> str:
        if not matches:
            return "No file name matched that search."
        return "Matching files: " + ", ".join(p.name for p in matches[:30])


def _human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def safe_join(root: os.PathLike[str], name: str) -> Path:  # pragma: no cover - convenience
    return FileManager(Path(root)).resolve(name)

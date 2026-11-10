"""Files folder: sandboxing, creation, never overwriting."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.errors import NotFoundError, UnsafeInputError, ValidationError
from jarvis.features.files import FileManager


@pytest.fixture
def manager(tmp_path: Path) -> FileManager:
    return FileManager(tmp_path / "files")


def test_root_is_created(manager: FileManager):
    assert manager.root.is_dir()


def test_create_and_read(manager: FileManager):
    manager.create("todo.txt", "buy milk")
    assert manager.read("todo.txt").strip() == "buy milk"


def test_create_never_overwrites(manager: FileManager):
    manager.create("todo.txt", "first")
    with pytest.raises(ValidationError):
        manager.create("todo.txt", "second")
    assert manager.read("todo.txt").strip() == "first"


def test_missing_file_raises(manager: FileManager):
    with pytest.raises(NotFoundError):
        manager.read("nope.txt")


@pytest.mark.parametrize(
    "name",
    ["../escape.txt", "..\\escape.txt", "/etc/passwd", "C:\\Windows\\x.txt", "~/secret.txt", "a/b.txt"],
)
def test_traversal_is_blocked(manager: FileManager, name: str):
    with pytest.raises((UnsafeInputError, ValidationError)):
        manager.resolve(name)


@pytest.mark.parametrize("name", ["script.exe", "binary.bin", "archive.zip"])
def test_only_text_files(manager: FileManager, name: str):
    with pytest.raises(ValidationError):
        manager.resolve(name)


def test_extension_is_added(manager: FileManager):
    assert manager.clean_name("shopping") == "shopping.txt"


def test_list_and_search(manager: FileManager):
    manager.create("alpha.txt", "a")
    manager.create("beta.md", "b")
    names = [p.name for p in manager.list_files()]
    assert names == ["alpha.txt", "beta.md"]
    assert [p.name for p in manager.search("alp")] == ["alpha.txt"]


def test_describe_empty(manager: FileManager):
    assert "empty" in manager.describe_files()


def test_large_file_is_refused(manager: FileManager):
    path = manager.create("big.txt", "x")
    path.write_text("y" * 10, encoding="utf-8")
    with pytest.raises(ValidationError):
        manager.read("big.txt", max_bytes=5)

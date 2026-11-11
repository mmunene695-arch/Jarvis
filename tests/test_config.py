"""Configuration loading, validation and precedence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from jarvis.config import JarvisConfig, default_data_dir, load_config, write_default_config
from jarvis.errors import ConfigError


def test_defaults_are_sensible():
    cfg = JarvisConfig()
    assert cfg.wake_word == "hey jarvis"
    assert cfg.follow_up_seconds == 60.0
    assert cfg.response_target_seconds == 4.0
    assert cfg.research_enabled is True


def test_json_file_is_read(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"wake_word": "computer", "follow_up_seconds": 30, "cloud_answers": False}),
        encoding="utf-8",
    )
    cfg = load_config(env={"JARVIS_HOME": str(tmp_path)}, config_path=config_path)
    assert cfg.wake_word == "computer"
    assert cfg.follow_up_seconds == 30.0
    assert cfg.cloud_answers is False


def test_environment_overrides_file(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"wake_word": "computer"}), encoding="utf-8")
    cfg = load_config(
        env={"JARVIS_HOME": str(tmp_path), "JARVIS_WAKE_WORD": "hey jarvis"},
        config_path=config_path,
    )
    assert cfg.wake_word == "hey jarvis"


def test_unknown_key_is_rejected(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"nonsense": 1}), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(env={"JARVIS_HOME": str(tmp_path)}, config_path=config_path)


def test_invalid_json_is_rejected(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(env={"JARVIS_HOME": str(tmp_path)}, config_path=config_path)


@pytest.mark.parametrize(
    "env",
    [
        {"JARVIS_FOLLOW_UP_SECONDS": "0"},
        {"JARVIS_MEMORY_TURNS": "0"},
        {"JARVIS_GESTURE_DWELL_SECONDS": "0"},
        {"JARVIS_TTS": "telepathy"},
        {"JARVIS_RESEARCH": "maybe"},
    ],
)
def test_invalid_values_are_rejected(tmp_path: Path, env: dict[str, str]):
    with pytest.raises(ConfigError):
        load_config(env={"JARVIS_HOME": str(tmp_path), **env})


def test_default_data_dir_per_platform(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert default_data_dir({"HOME": "/home/x"}) == Path.home() / ".local" / "share" / "jarvis"
    assert default_data_dir({"JARVIS_HOME": "/tmp/jh"}) == Path("/tmp/jh")


def test_write_default_config_does_not_overwrite(tmp_path: Path):
    cfg = JarvisConfig(data_dir=tmp_path)
    path = write_default_config(cfg)
    original = path.read_text(encoding="utf-8")
    path.write_text(original.replace("hey jarvis", "computer"), encoding="utf-8")
    write_default_config(cfg, overwrite=False)
    assert "computer" in path.read_text(encoding="utf-8")


def test_ensure_directories(tmp_path: Path):
    cfg = JarvisConfig(data_dir=tmp_path / "nested" / "jarvis")
    cfg.ensure_directories()
    assert cfg.files_dir.is_dir()
    assert cfg.logs_dir.is_dir()

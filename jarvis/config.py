"""Configuration loading for JARVIS.

Precedence: built-in defaults < ``config.json`` < environment variables.
Configuration is immutable once loaded; call :func:`load_config` again to get a
fresh object.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from .errors import ConfigError

CONFIG_FILENAME = "config.json"

_TRUE = {"1", "true", "t", "yes", "y", "on"}
_FALSE = {"0", "false", "f", "no", "n", "off"}


def default_data_dir(env: Mapping[str, str] | None = None) -> Path:
    """Return the per-user data directory for the current platform."""
    env = os.environ if env is None else env
    override = env.get("JARVIS_HOME")
    if override:
        return Path(override).expanduser()
    if sys.platform.startswith("win"):
        base = env.get("APPDATA") or env.get("LOCALAPPDATA") or str(Path.home())
        return Path(base) / "Jarvis"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Jarvis"
    xdg = env.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "jarvis"
    return Path.home() / ".local" / "share" / "jarvis"


@dataclass(frozen=True)
class JarvisConfig:
    """Immutable runtime configuration."""

    assistant_name: str = "Jarvis"
    wake_word: str = "hey jarvis"
    follow_up_seconds: float = 60.0
    response_target_seconds: float = 4.0
    memory_turns: int = 20
    require_confirmation: bool = True
    screen_capture_confirmation: bool = True
    cloud_answers: bool = True
    research_enabled: bool = True
    tts_backend: str = "auto"
    stt_backend: str = "auto"
    gestures_enabled: bool = True
    gesture_dwell_seconds: float = 1.2
    startup_enabled: bool = False
    log_level: str = "INFO"
    data_dir: Path = field(default_factory=default_data_dir)

    # ------------------------------------------------------------------
    # Derived locations
    # ------------------------------------------------------------------
    @property
    def files_dir(self) -> Path:
        return self.data_dir / "files"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def audit_log_path(self) -> Path:
        return self.logs_dir / "audit.jsonl"

    @property
    def config_path(self) -> Path:
        return self.data_dir / CONFIG_FILENAME

    def ensure_directories(self) -> None:
        """Create the data directories. Safe to call repeatedly."""
        for path in (self.data_dir, self.files_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["data_dir"] = str(self.data_dir)
        return data

    def with_overrides(self, **changes: Any) -> JarvisConfig:
        """Return a copy of this configuration with ``changes`` applied."""
        unknown = set(changes) - {f.name for f in fields(self)}
        if unknown:
            raise ConfigError(f"unknown configuration key(s): {', '.join(sorted(unknown))}")
        return JarvisConfig(**{**self.as_dict_with_paths(), **changes})

    def as_dict_with_paths(self) -> dict[str, Any]:
        data = asdict(self)
        return data


_ENV_MAP: dict[str, str] = {
    "JARVIS_ASSISTANT_NAME": "assistant_name",
    "JARVIS_WAKE_WORD": "wake_word",
    "JARVIS_FOLLOW_UP_SECONDS": "follow_up_seconds",
    "JARVIS_RESPONSE_TARGET_SECONDS": "response_target_seconds",
    "JARVIS_MEMORY_TURNS": "memory_turns",
    "JARVIS_REQUIRE_CONFIRMATION": "require_confirmation",
    "JARVIS_SCREEN_CONFIRMATION": "screen_capture_confirmation",
    "JARVIS_CLOUD_ANSWERS": "cloud_answers",
    "JARVIS_RESEARCH": "research_enabled",
    "JARVIS_TTS": "tts_backend",
    "JARVIS_STT": "stt_backend",
    "JARVIS_GESTURES": "gestures_enabled",
    "JARVIS_GESTURE_DWELL_SECONDS": "gesture_dwell_seconds",
    "JARVIS_STARTUP": "startup_enabled",
    "JARVIS_LOG_LEVEL": "log_level",
}


def _as_bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE:
            return True
        if lowered in _FALSE:
            return False
    raise ConfigError(f"{key} must be a boolean, got {value!r}")


def _coerce(key: str, value: Any) -> Any:
    """Coerce a raw JSON/env value to the type of the dataclass default."""
    defaults = {f.name: f.default for f in fields(JarvisConfig) if f.default is not None}
    if key == "data_dir":
        return Path(str(value)).expanduser()
    target = type(defaults[key]) if key in defaults else str
    try:
        if target is bool:
            return _as_bool(value, key)
        if target is int:
            if isinstance(value, bool):
                raise ValueError
            return int(str(value).strip())
        if target is float:
            if isinstance(value, bool):
                raise ValueError
            return float(str(value).strip())
        if target is str:
            if not isinstance(value, str):
                raise ValueError
            return value.strip()
        if target is Path:
            return Path(str(value)).expanduser()
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{key} has an invalid value: {value!r}") from exc
    return value


def _validate(config: JarvisConfig) -> JarvisConfig:
    if not config.wake_word.strip():
        raise ConfigError("wake_word must not be empty")
    if config.follow_up_seconds <= 0:
        raise ConfigError("follow_up_seconds must be greater than zero")
    if config.response_target_seconds <= 0:
        raise ConfigError("response_target_seconds must be greater than zero")
    if config.memory_turns < 1:
        raise ConfigError("memory_turns must be at least 1")
    if config.gesture_dwell_seconds <= 0:
        raise ConfigError("gesture_dwell_seconds must be greater than zero")
    if config.gesture_dwell_seconds > 10:
        raise ConfigError("gesture_dwell_seconds must be 10 seconds or less")
    for key in ("tts_backend", "stt_backend"):
        if getattr(config, key) not in {"auto", "cloud", "local", "off"}:
            raise ConfigError(f"{key} must be one of auto, cloud, local, off")
    return config


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a JSON object")
    return raw


def load_config(
    env: Mapping[str, str] | None = None,
    config_path: str | os.PathLike[str] | None = None,
) -> JarvisConfig:
    """Load configuration from ``config.json`` and the environment."""
    env = os.environ if env is None else env
    data_dir = default_data_dir(env)
    path = Path(config_path).expanduser() if config_path else data_dir / CONFIG_FILENAME

    values: dict[str, Any] = {}
    known = {f.name for f in fields(JarvisConfig)}
    if path.is_file():
        raw = _read_json(path)
        for key, value in raw.items():
            if key not in known:
                raise ConfigError(f"unknown configuration key in {path}: {key}")
            values[key] = _coerce(key, value)

    for env_key, field_name in _ENV_MAP.items():
        if env_key in env:
            values[field_name] = _coerce(field_name, env[env_key])
    if "JARVIS_HOME" in env:
        values["data_dir"] = data_dir

    values.setdefault("data_dir", data_dir)
    return _validate(JarvisConfig(**values))


def write_default_config(config: JarvisConfig, *, overwrite: bool = False) -> Path:
    """Write ``config.json`` for the user. Refuses to overwrite by default."""
    config.ensure_directories()
    path = config.config_path
    if path.exists() and not overwrite:
        return path
    payload = config.as_dict()
    payload["data_dir"] = str(payload["data_dir"])
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path

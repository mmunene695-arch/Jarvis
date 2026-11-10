"""Shared fixtures. Every test runs fully offline in a temporary data folder."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CLEAN_ENV_KEYS = (
    "OPENAI_API_KEY",
    "JARVIS_LLM_API_KEY",
    "JARVIS_VISION_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GMAIL_REFRESH_TOKEN",
    "GMAIL_ACCESS_TOKEN",
    "GMAIL_CLIENT_ID",
    "GMAIL_CLIENT_SECRET",
    "WHATSAPP_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_FROM_NUMBER",
    "TWILIO_TO_NUMBER",
    "JARVIS_OFFLINE",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in CLEAN_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "jarvis-home"
    monkeypatch.setenv("JARVIS_HOME", str(home))
    return home


@pytest.fixture
def config(data_dir: Path):
    from jarvis.config import load_config

    cfg = load_config(env={"JARVIS_HOME": str(data_dir)})
    cfg.ensure_directories()
    return cfg


@pytest.fixture
def engine(config):
    from jarvis.engine import JarvisEngine

    return JarvisEngine(config)

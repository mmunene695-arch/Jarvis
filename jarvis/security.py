"""Secret redaction, audit logging and shell-command guardrails.

JARVIS never executes arbitrary shell commands. This module defines the
patterns used to detect and refuse shell-like requests, and the audit log that
records every state-changing action without leaking credentials.
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-+/=]+"), r"\1[redacted]"),
    (re.compile(r"(?i)((?:token|api[_-]?key|secret|password|passwd|auth|key)[\"']?\s*[:=]\s*[\"']?)[^\s,;\"'}&]+"), r"\1[redacted]"),
    (re.compile(r"(?i)\b[a-z0-9_.-]{0,24}(?:secret|token|apikey|api_key)[a-z0-9_.-]{0,24}\b(?=\s*$)"), "[redacted]"),
    (re.compile(r"\b(sk-[A-Za-z0-9]{8,})\b"), "[redacted]"),
    (re.compile(r"\b(AC[0-9a-fA-F]{32})\b"), "[redacted]"),
    (re.compile(r"\b(EAA[A-Za-z0-9]{8,})\b"), "[redacted]"),
)

_SHELL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(rm|rmdir|del|erase|format|mkfs|shutdown|reboot|halt|kill|killall|taskkill)\b\s+[-/\w]"),
    re.compile(r"(?i)\b(sudo|su|doas|runas)\b"),
    re.compile(r"(?i)\b(powershell|pwsh|cmd(\.exe)?\s+/c|bash\s+-c|sh\s+-c|zsh\s+-c)\b"),
    re.compile(r"(?i)\b(curl|wget)\b\s+\S+.*(\||>|--)"),
    re.compile(r"[|;&`$]\s*(\w+)"),
    re.compile(r"(?i)\b(nc|netcat|ncat|telnet)\b"),
    re.compile(r"(?i)\b(reg\s+add|reg\s+delete|sc\s+(create|delete|stop))\b"),
    re.compile(r"(?i)/etc/(passwd|shadow|sudoers)"),
    re.compile(r"(?i)\bchmod\s+[0-7]{3,4}\b"),
    re.compile(r"(?i)\b(eval|exec|os\.system|subprocess|system)\s*\("),
)


def redact_secrets(text: str) -> str:
    """Remove credentials from ``text`` before it is logged or spoken."""
    if not isinstance(text, str):
        return text
    result = text
    for pattern, replacement in _REDACTION_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


_SENSITIVE_KEY = re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd|auth|credential)")


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact string values in a mapping.

    Values of keys that look like credentials are replaced outright, and every
    remaining string is scanned for inline credentials.
    """
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str) and _SENSITIVE_KEY.search(str(key)):
            cleaned[key] = "[redacted]"
        elif isinstance(value, str):
            cleaned[key] = redact_secrets(value)
        elif isinstance(value, dict):
            cleaned[key] = redact_mapping(value)
        elif isinstance(value, (list, tuple)):
            cleaned[key] = [
                redact_mapping(item) if isinstance(item, dict) else redact_secrets(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


@dataclass(frozen=True)
class ShellGuardResult:
    allowed: bool
    reason: str = ""

    def __bool__(self) -> bool:  # pragma: no cover - convenience
        return self.allowed


@dataclass
class ShellGuard:
    """Detects phrasing that asks JARVIS to execute a shell command."""

    extra_patterns: tuple[re.Pattern[str], ...] = ()

    def check(self, text: str) -> ShellGuardResult:
        if not text or not text.strip():
            return ShellGuardResult(True)
        for pattern in _SHELL_PATTERNS + tuple(self.extra_patterns):
            if pattern.search(text):
                return ShellGuardResult(
                    False,
                    "I don't run shell commands, and I will not type commands into a terminal "
                    "for you. I can open an app, manage files in my own folder, or answer "
                    "questions instead.",
                )
        return ShellGuardResult(True)

    def is_shell_request(self, text: str) -> bool:
        return not self.check(text).allowed


@dataclass
class AuditLog:
    """Append-only JSONL audit log with credential redaction."""

    path: Path
    clock: Any = field(default=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, event: str, **fields: Any) -> dict[str, Any]:
        entry = redact_mapping({"event": event, "at": round(float(self.clock()), 3), **fields})
        line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return entry

    def entries(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-limit:] if limit else rows

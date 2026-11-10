"""Redaction, audit logging and the shell-command guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.security import AuditLog, ShellGuard, redact_mapping, redact_secrets


@pytest.mark.parametrize(
    "text",
    [
        "Authorization: Bearer abc123def456",
        "api_key=super-secret-value",
        "token: 1234567890abcdef",
        "password=hunter2",
        "sk-abcdefghijklmnop",
    ],
)
def test_redaction_hides_credentials(text: str):
    redacted = redact_secrets(text)
    assert "hunter2" not in redacted
    assert "super-secret-value" not in redacted
    assert "sk-abcdefghijklmnop" not in redacted
    assert "[redacted]" in redacted


def test_redact_mapping_is_recursive():
    data = {"outer": {"api_key": "abcdef123456"}, "list": ["token=zzz"]}
    cleaned = redact_mapping(data)
    assert "abcdef123456" not in str(cleaned)
    assert "zzz" not in str(cleaned)


@pytest.mark.parametrize(
    "command",
    [
        "run rm -rf /",
        "delete everything with sudo",
        "execute powershell -Command whoami",
        "bash -c 'echo hi'",
        "kill 1234",
        "chmod 777 secrets",
        "eval(open('x'))",
    ],
)
def test_shell_requests_are_blocked(command: str):
    assert ShellGuard().is_shell_request(command)


@pytest.mark.parametrize(
    "command",
    [
        "open notepad",
        "what is on my screen",
        "create file todo.txt with buy milk",
        "system status",
        "remind me to stretch in 10 minutes",
        "search for a job",
        "paint the room blue",
    ],
)
def test_normal_requests_are_allowed(command: str):
    assert ShellGuard().check(command).allowed


def test_audit_log_writes_and_redacts(tmp_path: Path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.record("request", command="api_key=abc123secret")
    entries = log.entries()
    assert entries[0]["event"] == "request"
    assert "abc123secret" not in (tmp_path / "audit.jsonl").read_text(encoding="utf-8")


def test_audit_log_survives_bad_lines(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    path.write_text('{"event": "ok"}\nnot json\n', encoding="utf-8")
    assert len(AuditLog(path).entries()) == 1

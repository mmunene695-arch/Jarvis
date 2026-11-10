"""Offline console and command-line interface."""

from __future__ import annotations

import io
import json

from jarvis.cli import build_parser, main
from jarvis.console import ConsoleApp


def run_console(engine, text: str) -> tuple[int, str]:
    stdin = io.StringIO(text)
    stdout = io.StringIO()
    code = ConsoleApp(engine, stdin=stdin, stdout=stdout, prompt="").run()
    return code, stdout.getvalue()


def test_console_answers_local_commands(engine):
    code, output = run_console(engine, "system status\nexit\n")
    assert code == 0
    assert "jarvis>" in output
    assert "Memory" in output or "could not" in output


def test_console_handles_empty_lines(engine):
    code, output = run_console(engine, "\n\nsystem status\nquit\n")
    assert code == 0


def test_console_handles_eof(engine):
    code, output = run_console(engine, "help\n")
    assert code == 0
    assert "Goodbye" in output


def test_console_prints_help(engine):
    _, output = run_console(engine, "help\nexit\n")
    assert "remind me" in output.lower()


def test_console_shows_confirmation_hint(engine):
    _, output = run_console(engine, "create file t.txt with hi\nexit\n")
    assert "say yes to confirm" in output


def test_console_confirmation_flow(engine):
    run_console(engine, "create file t.txt with hi\nyes\nexit\n")
    assert (engine.config.files_dir / "t.txt").exists()


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def test_parser_defaults():
    args = build_parser().parse_args([])
    assert args.console is False
    assert args.command is None


def test_cli_single_command(engine, capsys, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(engine.config.data_dir))
    code = main(["--command", "system status"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Memory" in out or "could" in out


def test_cli_json_output(engine, capsys, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(engine.config.data_dir))
    code = main(["--command", "help", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["action"] == "help"


def test_cli_init_config(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(tmp_path / "home"))
    code = main(["--init-config"])
    assert code == 0
    assert (tmp_path / "home" / "config.json").is_file()


def test_cli_doctor(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(tmp_path / "home"))
    code = main(["--doctor"])
    payload = json.loads(capsys.readouterr().out.split("\n\n")[0])
    assert code == 0
    assert "capabilities" in payload
    assert payload["integrations"]["gmail"] is False


def test_cli_config_path(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(tmp_path / "home"))
    assert main(["--print-config-path"]) == 0
    assert "config.json" in capsys.readouterr().out


def test_cli_reports_config_errors(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("JARVIS_HOME", str(tmp_path / "home"))
    bad = tmp_path / "bad.json"
    bad.write_text("{broken", encoding="utf-8")
    assert main(["--command", "help", "--config", str(bad)]) == 2
    assert "Configuration error" in capsys.readouterr().err

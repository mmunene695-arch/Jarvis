"""End-to-end behaviour of the intent router."""

from __future__ import annotations

import pytest

from jarvis.engine import JarvisEngine, is_confirmation, is_denial, normalise


# ----------------------------------------------------------------------
# Text normalisation
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Hey Jarvis, what time is it", "what time is it"),
        ("hey jarvis system status", "system status"),
        ("JARVIS help", "help"),
        ("  please open notepad ", "open notepad"),
        ("can you list apps", "list apps"),
    ],
)
def test_normalise(raw: str, expected: str):
    assert normalise(raw) == expected


@pytest.mark.parametrize("word", ["yes", "yeah", "confirm", "ok", "do it", "thumbs up"])
def test_confirmations(word: str):
    assert is_confirmation(word)


@pytest.mark.parametrize("word", ["no", "cancel", "stop", "never mind"])
def test_denials(word: str):
    assert is_denial(word)


# ----------------------------------------------------------------------
# Conversation basics
# ----------------------------------------------------------------------
def test_help_lists_capabilities(engine: JarvisEngine):
    reply = engine.ask("help")
    assert reply.action == "help"
    assert "files" in reply.text.lower()
    assert "shell" in reply.text.lower()


def test_identity(engine: JarvisEngine):
    assert "Jarvis" in engine.ask("who are you").text


def test_unknown_request_is_graceful(engine: JarvisEngine):
    reply = engine.ask("compose a symphony about the moon")
    assert reply.error
    assert "cloud answers" in reply.text


def test_empty_request_prompts(engine: JarvisEngine):
    assert "listening" in engine.ask("").text.lower()


def test_conversation_is_remembered(engine: JarvisEngine):
    engine.ask("save a note buy bread")
    assert "buy bread" in engine.memory.transcript()


def test_memory_cleared_on_reset(engine: JarvisEngine):
    engine.ask("help")
    engine.reset()
    assert engine.memory.is_empty
    assert engine.pending is None


# ----------------------------------------------------------------------
# Shell refusal
# ----------------------------------------------------------------------
@pytest.mark.parametrize("command", ["run rm -rf /", "delete my files with sudo", "execute powershell"])
def test_shell_commands_refused(engine: JarvisEngine, command: str):
    reply = engine.ask(command)
    assert reply.error
    assert "shell" in reply.text.lower()


# ----------------------------------------------------------------------
# Confirmation flow
# ----------------------------------------------------------------------
def test_file_creation_needs_confirmation(engine: JarvisEngine):
    reply = engine.ask("create file todo.txt with buy milk")
    assert reply.pending is not None
    assert not (engine.config.files_dir / "todo.txt").exists()
    confirmed = engine.confirm()
    assert (engine.config.files_dir / "todo.txt").exists()
    assert confirmed.error is False


def test_yes_confirms_pending_action(engine: JarvisEngine):
    engine.ask("create file notes.md with hello")
    reply = engine.ask("yes")
    assert (engine.config.files_dir / "notes.md").exists()
    assert engine.pending is None
    assert reply.error is False


def test_no_cancels_pending_action(engine: JarvisEngine):
    engine.ask("create file later.txt with hello")
    reply = engine.ask("no")
    assert not (engine.config.files_dir / "later.txt").exists()
    assert engine.pending is None
    assert "cancelled" in reply.text.lower()


def test_confirm_with_nothing_pending(engine: JarvisEngine):
    assert "nothing" in engine.ask("yes").text.lower()


def test_existing_file_is_not_overwritten(engine: JarvisEngine):
    (engine.config.files_dir / "keep.txt").write_text("original", encoding="utf-8")
    reply = engine.ask("create file keep.txt with new content")
    assert reply.error
    assert (engine.config.files_dir / "keep.txt").read_text(encoding="utf-8") == "original"


# ----------------------------------------------------------------------
# Notes, files, reminders through the engine
# ----------------------------------------------------------------------
def test_note_round_trip(engine: JarvisEngine):
    assert "saved" in engine.ask("save a note buy milk").text.lower()
    assert "buy milk" in engine.ask("list notes").text


def test_note_search_through_engine(engine: JarvisEngine):
    engine.ask("save a note call the dentist on friday")
    assert "dentist" in engine.ask("search notes for dentist").text


def test_reminder_round_trip(engine: JarvisEngine):
    engine.ask("remind me to drink water in 5 minutes")
    assert "drink water" in engine.ask("list reminders").text


def test_read_file_through_engine(engine: JarvisEngine):
    engine.file_manager.create("hello.txt", "hello there")
    assert "hello there" in engine.ask("read file hello.txt").text


def test_system_status(engine: JarvisEngine):
    reply = engine.ask("system status")
    assert reply.action == "system.status"
    assert "CPU" in reply.text


@pytest.mark.parametrize(
    "command,action",
    [
        ("how much memory is free", "system.memory"),
        ("battery status", "system.battery"),
        ("cpu usage", "system.cpu"),
        ("free disk space", "system.disk"),
        ("which os is this", "system.platform"),
    ],
)
def test_system_subcommands(engine: JarvisEngine, command: str, action: str):
    assert engine.ask(command).action == action


# ----------------------------------------------------------------------
# Apps / urls
# ----------------------------------------------------------------------
def test_list_apps(engine: JarvisEngine):
    assert "known app" in engine.ask("list apps").text.lower() or "website" in engine.ask("list apps").text.lower()


def test_open_url_needs_confirmation(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    opened: list[str] = []
    monkeypatch.setattr("jarvis.features.apps.webbrowser.open_new_tab", lambda url: opened.append(url) or True)
    engine.ask("open youtube")
    assert opened == []
    engine.confirm()
    assert opened == ["https://www.youtube.com"]


def test_unknown_app_message(engine: JarvisEngine):
    reply = engine.ask("open zzznonexistentapp")
    assert reply.error
    assert "list apps" in reply.text


def test_terminal_is_not_scripted(engine: JarvisEngine):
    reply = engine.ask("open powershell")
    assert reply.error
    assert "will not type commands" in reply.text


# ----------------------------------------------------------------------
# Screen, research, integrations without credentials
# ----------------------------------------------------------------------
def test_screen_capture_requires_confirmation(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis.vision.pillow_available", lambda: True)
    monkeypatch.setattr("jarvis.vision.online_available", lambda *a, **k: True)
    reply = engine.ask("what is on my screen")
    assert reply.pending is not None
    assert "confirmation" in reply.text.lower()
    assert "vision" in reply.pending.description


def test_screen_capture_reports_missing_dependency(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis.vision.pillow_available", lambda: False)
    reply = engine.ask("what is on my screen")
    assert reply.error
    assert "pillow" in reply.text.lower()


def test_gmail_without_credentials(engine: JarvisEngine):
    reply = engine.ask("check my gmail")
    assert reply.error
    assert "Gmail is not connected" in reply.text


def test_whatsapp_without_credentials(engine: JarvisEngine):
    reply = engine.ask("send a whatsapp message to +254700000000 saying hello")
    assert reply.error
    assert "not configured" in reply.text


def test_sms_without_credentials(engine: JarvisEngine):
    reply = engine.ask("send sms to +254700000000 saying hello")
    assert reply.error
    assert "not configured" in reply.text


def test_call_without_credentials(engine: JarvisEngine):
    reply = engine.ask("call +254700000000")
    assert reply.error
    assert "not configured" in reply.text.lower()


def test_research_offline_is_actionable(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    import jarvis.features.knowledge as kb
    from jarvis.errors import NetworkError

    def boom(*_a, **_k):
        raise NetworkError("I cannot reach the search service. Check your internet connection.")

    monkeypatch.setattr(kb.research_module, "search", boom)
    reply = engine.ask("research solid state batteries")
    assert reply.error
    assert "internet" in reply.text.lower()


# ----------------------------------------------------------------------
# Gestures
# ----------------------------------------------------------------------
def test_gesture_mode_requires_optional_dependency(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis.gestures.available", lambda: False)
    reply = engine.ask("activate gesture mode")
    assert reply.error
    assert "vision" in reply.text


def test_gesture_mode_toggles(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis.gestures.available", lambda: True)
    monkeypatch.setattr("jarvis.gestures.launch_preview", lambda *a, **k: True)
    monkeypatch.setattr("jarvis.gestures.stop_preview", lambda: None)
    assert "on" in engine.ask("activate gesture mode").text.lower()
    assert engine.gesture_mode
    assert "off" in engine.ask("deactivate gesture mode").text.lower()
    assert not engine.gesture_mode


def test_gesture_cannot_create_message(engine: JarvisEngine):
    engine.gesture_mode = True
    reply = engine.gesture_event("thumbs up")
    assert reply.action == "gestures.confirm"
    assert "already waiting" in reply.text
    assert engine.pending is None


def test_gesture_confirms_pending(engine: JarvisEngine):
    engine.gesture_mode = True
    engine.ask("create file g.txt with hi")
    assert engine.pending is not None
    engine.gesture_event("thumbs up")
    assert (engine.config.files_dir / "g.txt").exists()


def test_gesture_fist_cancels(engine: JarvisEngine):
    engine.gesture_mode = True
    engine.ask("create file c.txt with hi")
    engine.gesture_event("fist")
    assert engine.pending is None
    assert not (engine.config.files_dir / "c.txt").exists()


def test_gesture_palm_pauses(engine: JarvisEngine):
    engine.gesture_mode = True
    engine.gesture_event("open palm")
    assert engine.gesture_paused is True
    engine.ask("resume gesture recognition")
    assert engine.gesture_paused is False


def test_gesture_ignored_when_mode_off(engine: JarvisEngine):
    assert engine.gesture_event("fist").action == "gestures.ignored"


# ----------------------------------------------------------------------
# Response target and audit
# ----------------------------------------------------------------------
def test_local_reply_is_fast(engine: JarvisEngine):
    reply = engine.ask("system status")
    assert reply.elapsed < engine.config.response_target_seconds


def test_audit_log_records_requests(engine: JarvisEngine):
    engine.ask("help")
    events = [entry["event"] for entry in engine.audit.entries()]
    assert "request" in events


def test_stop_command(engine: JarvisEngine):
    engine.ask("jarvis go to sleep")
    assert engine.running is False


def test_reminder_alerts_while_running(engine: JarvisEngine):
    spoken: list[str] = []
    engine.on_reply = spoken.append
    engine.reminders.add("drink water", delay_seconds=0)
    assert engine.reminders.poll()
    assert spoken and "drink water" in spoken[0]


def test_gesture_mode_connects_the_camera_callback(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    captured = {}
    monkeypatch.setattr("jarvis.gestures.available", lambda: True)
    monkeypatch.setattr(
        "jarvis.gestures.launch_preview",
        lambda callback=None, dwell_seconds=1.2: captured.setdefault("cb", callback) is None,
    )
    monkeypatch.setattr("jarvis.gestures.stop_preview", lambda: None)
    engine.ask("activate gesture mode")
    assert captured["cb"] == engine.gesture_event


def test_settings_page_is_not_treated_as_an_app(engine: JarvisEngine, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis.features.windows_control.is_windows", lambda: True)
    monkeypatch.setattr("jarvis.features.windows_control.open_settings", lambda page: f"opened {page}")
    reply = engine.ask("open bluetooth settings")
    assert reply.pending is not None
    assert "bluetooth" in reply.pending.description.lower()
    assert "opened bluetooth" in engine.confirm().text

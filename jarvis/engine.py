"""Intent router: turns a spoken or typed request into a reply and an action.

The engine is deliberately deterministic and dependency-free so it can be unit
tested without a microphone, a network connection or a desktop session. Every
state-changing action is staged as a :class:`PendingAction` and only performed
after an explicit confirmation.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from . import features
from .config import JarvisConfig
from .errors import JarvisError, ValidationError
from .memory import ShortTermMemory
from .security import AuditLog, ShellGuard


class Speaker(Protocol):  # pragma: no cover - structural typing only
    def say(self, text: str) -> None: ...


@dataclass
class Reply:
    """The outcome of one request."""

    text: str
    spoken: bool = False
    action: str | None = None
    pending: PendingAction | None = None
    error: bool = False
    elapsed: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "spoken": self.spoken,
            "action": self.action,
            "pending": self.pending.describe() if self.pending else None,
            "error": self.error,
            "elapsed": round(self.elapsed, 4),
            "data": self.data,
        }


@dataclass
class PendingAction:
    """An action that changes state and is waiting for confirmation."""

    name: str
    description: str
    run: Callable[[], str]
    kind: str = "generic"
    created_at: float = field(default_factory=time.time)

    def confirm(self) -> str:
        return self.run()

    def describe(self) -> str:
        return f"{self.name}: {self.description}"


_WAKE_PREFIX = re.compile(
    r"^\s*(?:hey|hi|ok|okay|yo)?\s*(?:jarvis|jervis|jarvis\.)\s*[,:.]?\s*", re.IGNORECASE
)

_CONFIRM_WORDS = {
    "yes",
    "yeah",
    "yep",
    "sure",
    "ok",
    "okay",
    "confirm",
    "confirmed",
    "do it",
    "go ahead",
    "proceed",
    "affirmative",
    "thumbs up",
    "submit",
}
_DENY_WORDS = {
    "no",
    "nope",
    "cancel",
    "stop",
    "abort",
    "don't",
    "dont",
    "never mind",
    "nevermind",
    "negative",
}

_POLITE_PREFIX = re.compile(
    r"^(?:please|kindly|jarvis[,\s]+|can you|could you|would you|will you|i want you to|"
    r"i'd like you to|go ahead and|just)\s+",
    re.IGNORECASE,
)


def normalise(text: str) -> str:
    """Lowercase, strip the wake word and collapse whitespace."""
    if text is None:
        raise ValidationError("no input received")
    cleaned = _WAKE_PREFIX.sub("", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = _POLITE_PREFIX.sub("", cleaned).strip()
    return cleaned


def is_confirmation(text: str) -> bool:
    token = normalise(text).strip(" .!?").lower()
    return token in _CONFIRM_WORDS


def is_denial(text: str) -> bool:
    token = normalise(text).strip(" .!?").lower()
    return token in _DENY_WORDS


class JarvisEngine:
    """Routes requests to local features and integrations."""

    def __init__(
        self,
        config: JarvisConfig | None = None,
        *,
        knowledge: Any = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config or JarvisConfig()
        self.config.ensure_directories()
        self.memory = ShortTermMemory(max_turns=self.config.memory_turns)
        self.audit = AuditLog(self.config.audit_log_path)
        self.guard = ShellGuard()
        self.clock = clock
        self.pending: PendingAction | None = None
        self.running = True
        self.gesture_mode = False
        self.gesture_paused = False

        self.file_manager = features.FileManager(self.config.files_dir)
        self.notes = features.NoteStore(self.config.data_dir / "notes.json")
        self.reminders = features.ReminderStore(self.config.data_dir / "reminders.json")
        self.knowledge = knowledge if knowledge is not None else features.KnowledgeBase(
            self.config, audit=self.audit
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ask(self, text: str, *, speak: Speaker | None = None) -> Reply:
        """Handle one request and optionally speak the reply."""
        started = self.clock()
        reply = self._dispatch(text)
        reply.elapsed = self.clock() - started
        if speak is not None and reply.text:
            try:
                speak.say(reply.text)
                reply.spoken = True
            except Exception:  # pragma: no cover - audio is best effort
                reply.spoken = False
        return reply

    def handle(self, text: str, *, speak: Speaker | None = None) -> Reply:
        """Alias for :meth:`ask`."""
        return self.ask(text, speak=speak)

    def confirm(self) -> Reply:
        """Run the pending action, if any."""
        started = self.clock()
        if self.pending is None:
            reply = Reply("There is nothing waiting for confirmation.", action="confirm")
        else:
            action, self.pending = self.pending, None
            try:
                message = action.run()
                self.audit.record("action.confirmed", action=action.name, kind=action.kind)
                reply = Reply(message or "Done.", action=action.name)
            except JarvisError as exc:
                self.audit.record("action.failed", action=action.name, error=str(exc))
                reply = Reply(str(exc), action=action.name, error=True)
        reply.elapsed = self.clock() - started
        self.memory.exchange("<confirm>", reply.text)
        return reply

    def cancel(self) -> Reply:
        """Discard the pending action."""
        if self.pending is None:
            return Reply("There is nothing to cancel.", action="cancel")
        name = self.pending.name
        self.pending = None
        self.audit.record("action.cancelled", action=name)
        reply = Reply("Cancelled. I did not change anything.", action="cancel")
        self.memory.exchange("<cancel>", reply.text)
        return reply

    def reset(self) -> None:
        self.memory.clear()
        self.pending = None

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def _dispatch(self, raw: str) -> Reply:
        try:
            command = normalise(raw)
        except ValidationError as exc:
            return Reply(str(exc), error=True)

        if not command:
            return Reply(
                'I am listening. Try "what is on my screen", "add a note", or "system status".'
            )

        self.audit.record("request", command=command)
        self.memory.add("user", command)

        guard = self.guard.check(command)
        if not guard.allowed:
            self.audit.record("request.blocked", reason="shell")
            return self._remember(Reply(guard.reason, action="blocked", error=True))

        # Confirm / cancel first, so "yes" always means "the thing you asked".
        if is_confirmation(command) and self.pending is not None:
            return self.confirm()
        if is_denial(command) and self.pending is not None:
            return self.cancel()

        for handler in self._handlers():
            try:
                reply = handler(command)
            except JarvisError as exc:
                return self._remember(
                    Reply(str(exc), error=True, action=f"error.{handler.__name__.strip('_')}")
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.audit.record("request.error", error=repr(exc))
                return self._remember(
                    Reply(
                        "Something went wrong while handling that request. "
                        f"The details were written to the audit log ({type(exc).__name__}).",
                        error=True,
                    )
                )
            if reply is not None:
                return self._remember(reply)

        return self._remember(self._fallback(command))

    def _remember(self, reply: Reply) -> Reply:
        self.memory.add("assistant", reply.text)
        return reply

    def _handlers(self) -> Iterable[Callable[[str], Reply | None]]:
        return (
            self._help,
            self._identity,
            self._stop,
            self._confirm_word,
            self._reminders,
            self._notes,
            self._files,
            self._knowledge,
            self._system,
            self._open_targets,
            self._screen,
            self._research,
            self._settings,
            self._volume,
            self._bluetooth,
            self._startup,
            self._gestures,
            self._gmail,
            self._whatsapp,
            self._sms,
            self._calls,
            self._time,
        )

    # ------------------------------------------------------------------
    # Built-in conversation
    # ------------------------------------------------------------------
    def _help(self, command: str) -> Reply | None:
        if not re.search(r"^(help|what can you do|commands|list commands)\b", command):
            return None
        lines = [
            "Here is what I can do offline or with internet:",
            "• Status: memory, battery, CPU and disk.",
            "• Files: list, search, read or create text files in my folder.",
            "• Notes and knowledge: save notes, search what I saved.",
            "• Reminders: add or list reminders while I am running.",
            "• Apps and sites: open an app, list apps, open a website.",
            "• Screen: describe what is visible, after you confirm the capture.",
            "• Research: search the web with citations, then optionally save it.",
            "• Gestures: activate or deactivate gesture mode.",
            "• Accounts: Gmail unread mail, WhatsApp, SMS and calls.",
            "I do not run shell commands or install software.",
        ]
        return Reply("\n".join(lines), action="help")

    def _identity(self, command: str) -> Reply | None:
        if not re.search(r"\b(who are you|what are you|your name|introduce yourself)\b", command):
            return None
        return Reply(
            f"I am {self.config.assistant_name} version 0.2, a local-first desktop assistant. "
            "Say \"hey jarvis\" to wake me, or type in the offline console.",
            action="identity",
        )

    def _stop(self, command: str) -> Reply | None:
        if not re.search(r"\b(goodbye|bye|stop listening|exit|quit|shut down|go to sleep)\b", command):
            return None
        if not re.search(r"\b(jarvis|yourself|stop listening|go to sleep)\b", command):
            return None
        self.running = False
        return Reply("Going back to standby. Say \"hey jarvis\" when you need me.", action="stop")

    def _confirm_word(self, command: str) -> Reply | None:
        if is_confirmation(command):
            return Reply("There is nothing waiting for confirmation.", action="confirm")
        if is_denial(command):
            return Reply("Nothing to cancel.", action="cancel")
        return None

    def _time(self, command: str) -> Reply | None:
        if not re.search(r"\b(what time|what's the time|the time|todays date|today's date|what date)\b", command):
            return None
        now = time.strftime("%H:%M")
        date = time.strftime("%A, %d %B %Y")
        return Reply(f"It is {now} on {date}.", action="time")

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------
    def _reminders(self, command: str) -> Reply | None:
        if re.search(r"\b(list (my )?reminders|show (my )?reminders|what are my reminders)\b", command):
            return Reply(self.reminders.describe(), action="reminders.list")
        if re.search(r"\b(clear|delete|remove) (all )?(my )?reminders\b", command):
            if not self.reminders.all():
                return Reply("You have no reminders.", action="reminders.clear")
            action = PendingAction(
                name="reminders.clear",
                description="delete every saved reminder",
                kind="destructive",
                run=lambda: (
                    self.reminders.clear() or "All reminders deleted."
                ),
            )
            return self._stage(action)
        match = re.search(
            r"\bremind me (?:to|that|about)\s+(?P<text>.+?)(?:\s+(?:in|after)\s+(?P<delay>.+))?$",
            command,
        )
        if not match:
            match = re.search(r"\badd (?:a )?reminder\s+(?:to\s+)?(?P<text>.+)$", command)
            if not match:
                return None
            text = match.group("text")
            delay = None
        else:
            text = match.group("text")
            delay = match.groupdict().get("delay")
        if not text.strip():
            return Reply("What should I remind you about?", error=True)
        due = self.reminders.parse_delay(delay) if delay else 0.0
        reminder = self.reminders.add(text.strip(), delay_seconds=due)
        when = "now" if due <= 0 else f"in {self.reminders.humanise(due)}"
        self.audit.record("reminder.created", reminder_id=reminder["id"])
        return Reply(f"Reminder saved: {reminder['text']} ({when}).", action="reminders.add")

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------
    def _notes(self, command: str) -> Reply | None:
        save = re.search(
            r"\b(?:save|write|take|make|add|create) (?:a |the )?note(?: (?:that|saying|about))?\s*[:,-]?\s*(?P<text>.+)$",
            command,
        )
        if save:
            text = save.group("text").strip()
            if not text:
                return Reply("What should the note say?", error=True)
            note = self.notes.add(text)
            self.audit.record("note.created", note_id=note["id"])
            return Reply(f"Note saved ({note['id']}): {note['text']}", action="notes.add")
        search = re.search(r"\b(?:find|search) (?:my )?notes (?:for|about)\s+(?P<query>.+)$", command)
        if search:
            found = self.notes.search(search.group("query"))
            return Reply(self.notes.describe(found), action="notes.search")
        if re.search(r"\b(list|show|read) (?:my )?notes\b", command):
            return Reply(self.notes.describe(self.notes.all()), action="notes.list")
        return None

    # ------------------------------------------------------------------
    # Files
    # ------------------------------------------------------------------
    def _files(self, command: str) -> Reply | None:
        if re.search(r"\b(list|show) (?:the )?(?:files|my files|files folder)\b", command):
            return Reply(self.file_manager.describe_files(), action="files.list")
        search = re.search(r"\bsearch (?:the )?files? (?:for|named)\s+(?P<query>.+)$", command)
        if not search:
            search = re.search(r"\bfind (?:a )?file (?:called|named|with name)\s+(?P<query>.+)$", command)
        if search:
            matches = self.file_manager.search(search.group("query").strip())
            return Reply(self.file_manager.describe_matches(matches), action="files.search")
        read = re.search(r"\bread (?:the )?file\s+(?P<name>.+)$", command)
        if read:
            name = self.file_manager.clean_name(read.group("name"))
            content = self.file_manager.read(name)
            preview = content if len(content) <= 1200 else content[:1200] + "…"
            return Reply(f"{name} says:\n{preview}", action="files.read")
        create = re.search(
            r"\bcreate (?:a )?file(?: called| named)?\s+(?P<name>[\w.\- ]+?\.(?:txt|md|json|csv|log))"
            r"(?: (?:with|containing|saying)\s+(?P<body>.+))?$",
            command,
        )
        if create:
            name = create.group("name").strip()
            body = (create.group("body") or "").strip()
            if self.file_manager.exists(name):
                return Reply(
                    f"{name} already exists, so I will not overwrite it. "
                    "Ask me to read it, or choose another name.",
                    action="files.create",
                    error=True,
                )
            action = PendingAction(
                name="files.create",
                description=f"create the file {name} in the Jarvis files folder",
                kind="filesystem",
                run=lambda: self._run_create_file(name, body),
            )
            return self._stage(action)
        return None

    def _run_create_file(self, name: str, body: str) -> str:
        path = self.file_manager.create(name, body)
        return f"Created {path.name} in {self.file_manager.root}."

    # ------------------------------------------------------------------
    # Knowledge base
    # ------------------------------------------------------------------
    def _knowledge(self, command: str) -> Reply | None:
        save = re.search(
            r"\b(?:save|store) (?:this |that )?(?:to|in) (?:my )?knowledge(?:\s+base)?(?:\s+(?:as|titled|called)\s+(?P<title>.+))?$",
            command,
        )
        if save:
            title = (save.group("title") or "").strip()
            last = self.memory.recent(3)
            source = next((m.content for m in reversed(last) if m.role == "assistant"), "")
            if not source and self.knowledge.last_research:
                source = self.knowledge.last_research.get("summary", "")
            if not source:
                return Reply("I have nothing recent to save yet. Ask me a research question first.", error=True)
            entry = self.knowledge.add(title or "Saved note", source)
            return Reply(f"Saved to knowledge as {entry['id']}.", action="knowledge.add")
        search = re.search(
            r"\b(?:search|find|look up|what do you know about)\s+(?:my )?(?:knowledge|notes|memory)(?:\s+(?:for|about))?\s*(?P<query>.*)$",
            command,
        )
        if search and (search.group("query") or "knowledge" in command):
            query = search.group("query").strip() or "all"
            results = self.knowledge.search(query)
            return Reply(self.knowledge.describe(results, query), action="knowledge.search")
        return None

    # ------------------------------------------------------------------
    # System information
    # ------------------------------------------------------------------
    def _system(self, command: str) -> Reply | None:
        if re.search(r"\b(memory|ram)\b", command) and re.search(
            r"\b(free|available|status|usage|how much|system|computer)\b", command
        ):
            return Reply(features.system_info.memory_report(), action="system.memory")
        if re.search(r"\bbattery\b", command):
            return Reply(features.system_info.battery_report(), action="system.battery")
        if re.search(r"\b(cpu|processor|cores?)\b", command):
            return Reply(features.system_info.cpu_report(), action="system.cpu")
        if re.search(r"\b(disk|storage|space|ssd|hard drive)\b", command):
            return Reply(features.system_info.disk_report(), action="system.disk")
        if re.search(
            r"\b(system status|computer status|status report|how is my computer|system info|"
            r"system information|machine info)\b",
            command,
        ):
            return Reply(features.system_info.full_report(), action="system.status")
        if re.search(r"\b(what platform|what os|operating system|which os|my platform)\b", command):
            return Reply(features.system_info.platform_report(), action="system.platform")
        if re.search(r"\b(uptime|how long has .* been (on|running))\b", command):
            return Reply(features.system_info.uptime_report(), action="system.uptime")
        return None

    # ------------------------------------------------------------------
    # Apps, windows, websites
    # ------------------------------------------------------------------
    def _open_targets(self, command: str) -> Reply | None:
        if re.search(r"\b(list|show|what) (?:my )?(available )?apps\b", command) or re.search(
            r"\bwhat apps (?:are available|can you open)\b", command
        ):
            return Reply(features.apps.describe_available(), action="apps.list")
        match = re.search(r"\b(?:open|launch|start|run)\s+(?:the\s+|my\s+)?(?P<target>.+?)(?:\s+app|\s+application)?$", command)
        if not match:
            return None
        target = match.group("target").strip().strip(".?!")
        if not target:
            return None
        if target.split(".")[0].lower() in {"shell", "terminal", "powershell", "cmd", "bash", "zsh", "command prompt"}:
            return Reply(
                "I can open a terminal window, but I will not type commands into it for you.",
                action="blocked",
                error=True,
            )
        kind, resolved = features.apps.resolve(target)
        if kind == "url":
            action = PendingAction(
                name="apps.open_url",
                description=f"open {resolved} in your default browser",
                kind="network",
                run=lambda: features.apps.open_url(resolved),
            )
            return self._stage(action, prefix=f"I can open {resolved} in your browser.")
        if kind == "app":
            return Reply(features.apps.open_app(resolved), action="apps.open")
        return Reply(
            f'I could not find an app called "{target}". Say "list apps" to see what I can open.',
            action="apps.open",
            error=True,
        )

    # ------------------------------------------------------------------
    # Screen understanding
    # ------------------------------------------------------------------
    def _screen(self, command: str) -> Reply | None:
        if not re.search(
            r"\b(what(?:'s| is)? (?:on|visible on) (?:my |the )?screen|analy[sz]e (?:my |the )?screen|"
            r"describe (?:my |the )?screen|screen capture|screenshot|look at my screen|what do you see)\b",
            command,
        ):
            return None
        from . import vision

        if not vision.pillow_available():
            return Reply(
                "Screen analysis needs Pillow. Install the vision extra: "
                'pip install "jarvis-assistant[vision]".',
                action="screen",
                error=True,
            )
        if not vision.online_available():
            return Reply(
                "Screen analysis also needs an online vision key. Set OPENAI_API_KEY or "
                "JARVIS_VISION_API_KEY. See INTEGRATIONS.md.",
                action="screen",
                error=True,
            )
        if self.config.screen_capture_confirmation:
            action = PendingAction(
                name="screen.capture",
                description="capture your screen once and send the image to the cloud vision model",
                kind="privacy",
                run=lambda: self._run_screen_analysis(),
            )
            return self._stage(action, prefix="Screen capture needs your confirmation.")
        return Reply(self._run_screen_analysis(), action="screen.capture")

    def _run_screen_analysis(self) -> str:
        from . import vision

        self.audit.record("screen.capture", provider="cloud")
        image = vision.capture_screen()
        return vision.analyse(image, prompt="Describe what is on this screen concisely.")

    # ------------------------------------------------------------------
    # Web research
    # ------------------------------------------------------------------
    def _research(self, command: str) -> Reply | None:
        if not self.config.research_enabled:
            return None
        match = re.search(
            r"\b(?:research|search (?:the )?(?:web|internet)|look up|google|find out about)\s+(?:for\s+)?(?P<query>.+)$",
            command,
        )
        if not match:
            if re.search(r"\b(research|web search)\b", command) and " save" not in command:
                return Reply('What should I research? For example: "research solid state batteries".', error=True)
            return None
        query = match.group("query").strip().strip(".?!")
        if not query:
            return Reply("What should I research?", error=True)
        result = self.knowledge.research(query)
        return Reply(result["summary"], action="research", data={"sources": result["sources"]})

    # ------------------------------------------------------------------
    # Windows settings and volume
    # ------------------------------------------------------------------
    def _settings(self, command: str) -> Reply | None:
        match = re.search(r"\bopen (?:the )?(?P<page>.+?) settings(?: page)?$", command)
        if not match:
            return None
        page = match.group("page").strip()
        if not features.windows_control.is_windows():
            return Reply("Settings pages can only be opened on Windows.", action="settings", error=True)
        action = PendingAction(
            name="settings.open",
            description=f"open the Windows {page} settings page",
            kind="system",
            run=lambda: features.windows_control.open_settings(page),
        )
        return self._stage(action)

    def _volume(self, command: str) -> Reply | None:
        match = re.search(r"\b(?:set|change|turn) (?:the )?volume (?:to|up to|down to)?\s*(?P<level>\d{1,3})\b", command)
        if match:
            level = int(match.group("level"))
            if not 0 <= level <= 100:
                return Reply("Volume must be between 0 and 100.", error=True)
            if not features.windows_control.is_windows():
                return Reply("Volume control is only implemented for Windows.", action="volume", error=True)
            action = PendingAction(
                name="volume.set",
                description=f"set the system volume to {level} percent",
                kind="system",
                run=lambda: features.windows_control.set_volume(level),
            )
            return self._stage(action)
        if re.search(r"\b(mute|unmute)\b", command):
            if not features.windows_control.is_windows():
                return Reply("Mute control is only implemented for Windows.", action="volume", error=True)
            mute = "unmute" not in command
            action = PendingAction(
                name="volume.mute",
                description=f"{'mute' if mute else 'unmute'} the system volume",
                kind="system",
                run=lambda: features.windows_control.set_mute(mute),
            )
            return self._stage(action)
        return None

    # ------------------------------------------------------------------
    # Bluetooth
    # ------------------------------------------------------------------
    def _bluetooth(self, command: str) -> Reply | None:
        if not re.search(r"\b(scan|search|look) for (?:nearby )?bluetooth\b|\bbluetooth (?:scan|devices)\b", command):
            return None
        devices = features.bluetooth.scan(timeout=6.0)
        return Reply(features.bluetooth.describe(devices), action="bluetooth.scan")

    # ------------------------------------------------------------------
    # Startup launcher
    # ------------------------------------------------------------------
    def _startup(self, command: str) -> Reply | None:
        if re.search(r"\b(enable|add|install|create)\b.*\bstartup\b", command) or re.search(
            r"\bstart jarvis (?:at|on) (?:sign in|login|startup)\b", command
        ):
            action = PendingAction(
                name="startup.enable",
                description="add a visible JARVIS launcher to your startup items",
                kind="system",
                run=lambda: features.startup.enable(),
            )
            return self._stage(action)
        if re.search(r"\b(disable|remove|delete|uninstall)\b.*\bstartup\b", command):
            action = PendingAction(
                name="startup.disable",
                description="remove the JARVIS startup launcher",
                kind="system",
                run=lambda: features.startup.disable(),
            )
            return self._stage(action)
        if re.search(r"\b(startup (status|enabled\?)|is startup (enabled|on))\b", command):
            return Reply(features.startup.status(), action="startup.status")
        return None

    # ------------------------------------------------------------------
    # Gestures
    # ------------------------------------------------------------------
    def _gestures(self, command: str) -> Reply | None:
        if re.search(r"\b(activate|enable|start|turn on) gesture( mode)?\b", command):
            from . import gestures

            if not self.config.gestures_enabled:
                return Reply("Gesture mode is disabled in the configuration.", action="gestures", error=True)
            if not gestures.available():
                return Reply(
                    "Gesture mode needs OpenCV and MediaPipe. Install the gesture extra: "
                    "pip install \"jarvis-assistant[vision]\".",
                    action="gestures",
                    error=True,
                )
            self.gesture_mode = True
            self.gesture_paused = False
            gestures.launch_preview()
            return Reply(
                "Gesture mode is on. The camera preview is visible and processing stays on this "
                "computer. Open palm pauses, fist cancels, thumbs-up confirms.",
                action="gestures.on",
            )
        if re.search(r"\b(deactivate|disable|stop|turn off) gesture( mode)?\b", command):
            from . import gestures

            self.gesture_mode = False
            gestures.stop_preview()
            return Reply("Gesture mode is off and the camera preview is closed.", action="gestures.off")
        if re.search(r"\b(pause|freeze) gesture( recognition| mode)?\b", command):
            self.gesture_paused = True
            return Reply("Gesture recognition paused. Say \"resume gesture recognition\" to continue.", action="gestures.pause")
        if re.search(r"\b(resume|continue|unpause) gesture( recognition| mode)?\b", command):
            self.gesture_paused = False
            return Reply("Gesture recognition resumed.", action="gestures.resume")
        return None

    def gesture_event(self, gesture: str) -> Reply:
        """Handle a dwell-confirmed gesture. Never creates a message or call."""
        from . import gestures as gesture_mod

        name = gesture_mod.canonical(gesture)
        self.audit.record("gesture.detected", gesture=name)
        if not self.gesture_mode:
            return Reply("Gesture mode is not active.", action="gestures.ignored")
        if name == "open_palm":
            self.gesture_paused = True
            return Reply("Gesture recognition paused.", action="gestures.pause")
        if name == "fist":
            if self.pending is None:
                return Reply("Nothing pending, so the fist did nothing.", action="gestures.cancel")
            return self.cancel()
        if name == "thumbs_up":
            if self.pending is None:
                return Reply(
                    "A thumbs-up can only confirm something that is already waiting. "
                    "Ask me to send a message or make a call first.",
                    action="gestures.confirm",
                )
            if self.pending.kind in {"message", "call"}:
                return self.confirm()
            return self.confirm()
        return Reply("I did not recognise that gesture.", action="gestures.unknown")

    # ------------------------------------------------------------------
    # Integrations
    # ------------------------------------------------------------------
    def _gmail(self, command: str) -> Reply | None:
        if not re.search(r"\b(gmail|unread (?:mail|email|e-mails?)|my (?:mail|inbox|email))\b", command):
            return None
        from .integrations import gmail

        try:
            return Reply(gmail.unread_summary(), action="gmail.unread")
        except JarvisError as exc:
            return Reply(str(exc), action="gmail.unread", error=True)

    def _whatsapp(self, command: str) -> Reply | None:
        match = re.search(
            r"\b(?:send|whatsapp|message)\s+(?P<target>(?:a\s+)?whatsapp(?:\s+message)?\s+to\s+[\w+\s@.\-]+?"
            r"|[\w+\s@.\-]+?\s+(?:on|via)\s+whatsapp)\b(?:.|\n)*?\b(?:saying|that says|with the message|message:)\s+(?P<body>.+)$",
            command,
        )
        if not match:
            if "whatsapp" in command and re.search(r"\bsend\b", command):
                return Reply(
                    'Give me the recipient and the text, for example: "send a WhatsApp message to '
                    '+254700000000 saying I am on my way".',
                    action="whatsapp",
                    error=True,
                )
            return None
        target = re.sub(r"\b(a\s+)?whatsapp(\s+message)?\s+to\s+|(\s+on|\s+via)\s+whatsapp\b", "", match.group("target")).strip()
        body = match.group("body").strip()
        from .integrations import whatsapp

        if not whatsapp.configured():
            return Reply(
                "WhatsApp is not configured yet. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID, "
                "then see INTEGRATIONS.md.",
                action="whatsapp",
                error=True,
            )
        action = PendingAction(
            name="whatsapp.send",
            description=f"send a WhatsApp message to {target} saying: {body}",
            kind="message",
            run=lambda: whatsapp.send_text(target, body),
        )
        return self._stage(action)

    def _sms(self, command: str) -> Reply | None:
        match = re.search(
            r"\b(?:send (?:an? )?s ?m ?s|text)\s+(?:to\s+)?(?P<target>[\w+\s@.\-]+?)"
            r"(?:\s+(?:saying|that says|with the message|message:)\s+(?P<body>.+))?$",
            command,
        )
        if not match:
            return None
        target = match.group("target").strip()
        body = (match.group("body") or "").strip() or "Message sent by Jarvis."
        from .integrations import twilio_client

        if not twilio_client.configured():
            return Reply(
                "SMS is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                "TWILIO_FROM_NUMBER and TWILIO_TO_NUMBER. See INTEGRATIONS.md.",
                action="sms",
                error=True,
            )
        action = PendingAction(
            name="sms.send",
            description=f"send an SMS to {target} saying: {body}",
            kind="message",
            run=lambda: twilio_client.send_sms(target, body),
        )
        return self._stage(action)

    def _calls(self, command: str) -> Reply | None:
        match = re.search(
            r"\b(?:call|phone)\s+(?P<target>\+\d[\d\s]{5,}|\d[\d\s]{7,})\b(.*)$", command
        )
        if not match:
            if re.search(r"\b(place a call|make a call|call someone)\b", command):
                return Reply(
                    "Give me the number, for example: \"call +254700000000\". I will ask for "
                    "confirmation before dialling.",
                    action="call",
                    error=True,
                )
            return None
        target = match.group("target").strip()
        from .integrations import twilio_client

        if not twilio_client.configured():
            return Reply(
                "Calls are not configured. Set the Twilio variables in INTEGRATIONS.md first.",
                action="call",
                error=True,
            )
        action = PendingAction(
            name="call.place",
            description=f"place an outbound call to {target} through Twilio (may incur charges)",
            kind="call",
            run=lambda: twilio_client.place_call(target),
        )
        return self._stage(action)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _stage(self, action: PendingAction, *, prefix: str = "") -> Reply:
        self.pending = action
        self.audit.record("action.staged", action=action.name, kind=action.kind)
        if prefix:
            question = f"{prefix.rstrip()} Say yes to confirm, or no to cancel."
        else:
            question = f"Confirm and I will {action.description}. Say yes or no."
        return Reply(question, action=action.name, pending=action)

    def _fallback(self, command: str) -> Reply:
        """No local skill matched: try the cloud model, else explain."""
        from . import cloud

        if self.config.cloud_answers and cloud.available():
            try:
                answer = cloud.complete(
                    command, context=self.memory.transcript(limit=6)
                )
                return Reply(answer, action="cloud.answer")
            except JarvisError as exc:
                return Reply(str(exc), action="cloud.answer", error=True)
        return Reply(
            "I could not match that to one of my local skills, and cloud answers are not "
            'configured. Try "help" to see what I can do offline.',
            action="unmatched",
            error=True,
        )

"""Full-screen terminal UI built on prompt_toolkit (optional extra)."""

from __future__ import annotations

from .engine import JarvisEngine

HEADER = "JARVIS v0.2 — offline-capable assistant. F1 help, Ctrl+C exit."


def run_tui(engine: JarvisEngine) -> int:  # pragma: no cover - interactive
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.shortcuts import print_formatted_text

    from .console import HELP_TEXT

    bindings = KeyBindings()

    @bindings.add("f1")
    def _help(event) -> None:  # noqa: ANN001
        event.app.current_buffer.insert_text("help")

    session: PromptSession = PromptSession(history=InMemoryHistory(), key_bindings=bindings)
    print_formatted_text(HTML(f"<b>{HEADER}</b>"))
    while True:
        try:
            line = session.prompt("you> ")
        except (KeyboardInterrupt, EOFError):
            print_formatted_text("Goodbye.")
            return 0
        if line.strip().lower() in {"exit", "quit"}:
            print_formatted_text("Goodbye.")
            return 0
        if line.strip().lower() in {"help", "?"}:
            print_formatted_text(HELP_TEXT)
            continue
        if not line.strip():
            continue
        reply = engine.ask(line)
        print_formatted_text(HTML(f"<ansigreen>jarvis&gt;</ansigreen> {reply.text}"))

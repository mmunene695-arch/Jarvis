"""Command-line entry point for JARVIS.

Examples::

    python -m jarvis --console
    python -m jarvis --command "system status"
    python -m jarvis --doctor
    python -m jarvis --voice
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import APP_NAME, __version__
from .config import JarvisConfig, load_config, write_default_config
from .console import ConsoleApp
from .engine import JarvisEngine
from .errors import JarvisError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS v0.2 - local-first voice assistant (Windows, Linux, macOS).",
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--console", action="store_true", help="start the offline text console (default)")
    mode.add_argument("--voice", action="store_true", help="start standby voice listening")
    mode.add_argument("--tui", action="store_true", help="start the full-screen terminal UI")
    mode.add_argument("--command", metavar="TEXT", help="run one command and exit")
    mode.add_argument("--doctor", action="store_true", help="check capabilities and configuration")
    mode.add_argument("--init-config", action="store_true", help="write a default config.json and exit")
    mode.add_argument(
        "--print-config-path",
        dest="print_config_path",
        action="store_true",
        help="print where config.json lives, then exit",
    )
    parser.add_argument("--yes", action="store_true", help="auto-confirm actions that need confirmation")
    parser.add_argument("--no-speak", action="store_true", help="never speak; print only")
    parser.add_argument("--speak", action="store_true", help="speak replies when in console or command mode")
    parser.add_argument("--config", metavar="PATH", help="use an explicit config.json")
    parser.add_argument("--json", action="store_true", help="print the reply as JSON")
    return parser


def _make_engine(args: argparse.Namespace) -> tuple[JarvisEngine, JarvisConfig]:
    config = load_config(config_path=args.config)
    engine = JarvisEngine(config)
    return engine, config


def _speaker(args: argparse.Namespace):
    if args.no_speak or not args.speak:
        return None
    from .voice import Speaker

    return Speaker("auto")


def cmd_doctor() -> int:
    from . import cloud, gestures, research, vision, voice  # noqa: F401
    from .features import startup, system_info
    from .integrations import gmail, twilio_client, whatsapp

    config = load_config()
    caps = voice.capabilities()
    report = {
        "version": __version__,
        "python": sys.version.split()[0],
        "platform": system_info.platform_info(),
        "data_dir": str(config.data_dir),
        "config_file": str(config.config_path),
        "config_exists": config.config_path.is_file(),
        "capabilities": {
            **caps,
            "screen_capture": vision.available(),
            "gesture_mode": gestures.available(),
            "research": config.research_enabled,
            "startup_launcher": startup.is_enabled(),
        },
        "integrations": {
            "gmail": gmail.GmailClient.from_env().configured(),
            "whatsapp": whatsapp.configured(),
            "twilio": twilio_client.configured(),
        },
    }
    print(json.dumps(report, indent=2))
    missing = [k for k, v in caps.items() if not v]
    print()
    if missing:
        print("Optional capabilities that are not available: " + ", ".join(missing))
        print('Install extras with: pip install "jarvis-assistant[all]"')
    else:
        print("All optional capabilities are available.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.print_config_path:
        print(load_config(config_path=args.config).config_path)
        return 0
    if args.doctor:
        return cmd_doctor()
    if args.init_config:
        config = load_config(config_path=args.config)
        path = write_default_config(config)
        print(f"Configuration written to {path}")
        return 0

    try:
        engine, config = _make_engine(args)
    except JarvisError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if args.command is not None:
        return _run_command(engine, args)

    if args.tui:
        try:
            from .tui import run_tui
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"The terminal UI needs prompt_toolkit: {exc}", file=sys.stderr)
            return 2
        return run_tui(engine)

    if args.voice:
        return _run_voice(engine, config, args)

    return ConsoleApp(engine).run()


def _run_command(engine: JarvisEngine, args: argparse.Namespace) -> int:
    speaker = _speaker(args)
    reply = engine.ask(args.command, speak=speaker)
    if args.yes and engine.pending is not None:
        reply = engine.confirm()
    if args.json:
        print(json.dumps(reply.as_dict(), indent=2, default=str))
    else:
        print(reply.text)
    return 0 if not reply.error else 1


def _run_voice(engine: JarvisEngine, config: JarvisConfig, args: argparse.Namespace) -> int:
    from .voice import Speaker, WakeWordMatcher, capabilities
    from .wake import VoiceSession

    caps = capabilities()
    if not caps["microphone"]:
        print(
            'The microphone needs the sounddevice library:\n'
            '  pip install "jarvis-assistant[voice]"\n'
            "Falling back to the offline console, which needs no microphone.",
            file=sys.stderr,
        )
        return ConsoleApp(engine).run()
    if not caps["cloud_stt"]:
        print(
            "Voice transcription uses an online service. Set OPENAI_API_KEY to enable it.\n"
            "Falling back to the offline console.",
            file=sys.stderr,
        )
        return ConsoleApp(engine).run()

    speaker = Speaker("off" if args.no_speak else config.tts_backend, config=config)
    session = VoiceSession(
        engine=engine,
        matcher=WakeWordMatcher(config.wake_word),
        speaker=speaker,
        follow_up_seconds=config.follow_up_seconds,
        printer=print,
    )
    session.run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""The offline text console.

Works with no microphone and no cloud services: local commands, notes, files,
reminders and saved knowledge are all available here.
"""

from __future__ import annotations

import sys
from typing import TextIO

from .engine import JarvisEngine
from .errors import JarvisError

BANNER = """\
JARVIS v0.2 — offline console
Type a command, or "help" for the list. "exit" leaves the console.
Local commands work without internet; research, Gmail, WhatsApp, SMS and calls need it.
"""

HELP_TEXT = """\
Conversation
  help / what can you do        show this list
  hello                         a quick check-in
  what time is it               current time and date
  exit                          leave the console

Computer
  system status                 memory, battery, CPU, disk
  how much memory is free       memory only
  battery status                battery only
  cpu usage                     processor only
  free disk space               disk only

Files (inside the Jarvis files folder)
  list files                    list text files
  search files for notes        search by file name
  read file todo.txt            read a text file
  create file todo.txt with buy milk   create (never overwrites)

Notes and knowledge
  save a note buy milk          store a note locally
  list notes                    show saved notes
  search notes for milk         search notes
  search knowledge for energy   search everything you saved
  save this to knowledge        store the last research result

Reminders
  remind me to stretch in 10 minutes
  list reminders

Apps, screen and web (internet for screen/web)
  list apps                     apps JARVIS can launch
  open notepad                  launch an app
  open github.com               open a website (asks first)
  what is on my screen          capture + analyse (asks first)
  research solid state batteries

Gestures and Windows
  activate gesture mode / deactivate gesture mode
  open bluetooth settings       Windows only
  set volume to 30              Windows only
  scan for bluetooth devices
  enable startup / disable startup / startup status

Accounts (need setup, see INTEGRATIONS.md)
  check my gmail
  send a whatsapp message to +254700000000 saying hello
  send sms to +254700000000 saying hello
  call +254700000000

Confirmation
  yes / confirm                 run the action waiting for confirmation
  no / cancel                   discard it
"""


class ConsoleApp:
    """Reads commands from a stream and prints replies."""

    def __init__(
        self,
        engine: JarvisEngine,
        *,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        prompt: str = "you> ",
    ) -> None:
        self.engine = engine
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.prompt = prompt

    def _write(self, text: str = "") -> None:
        self.stdout.write(text + "\n")
        try:
            self.stdout.flush()
        except Exception:
            pass

    def run(self, *, banner: bool = True) -> int:
        if banner:
            self._write(BANNER)
        while True:
            try:
                self.stdout.write(self.prompt)
                self.stdout.flush()
                line = self.stdin.readline()
            except (KeyboardInterrupt, EOFError):
                self._write("\nGoodbye.")
                return 0
            if not line:
                self._write("Goodbye.")
                return 0
            command = line.strip()
            if not command:
                continue
            if command.lower() in {"exit", "quit", "q", "bye"}:
                self._write("Goodbye.")
                return 0
            if command.lower() in {"help", "?"}:
                self._write(HELP_TEXT)
                continue
            try:
                reply = self.engine.ask(command)
            except JarvisError as exc:
                self._write(f"jarvis> {exc}")
                continue
            self._write(f"jarvis> {reply.text}")
            if self.engine.pending is not None:
                self._write("        (say yes to confirm, or no to cancel)")

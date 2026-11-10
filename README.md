# JARVIS v0.2

A local-first desktop assistant for **Windows, Linux and macOS**. Say **“Hey Jarvis”**
to wake it, or use the offline text console when you have no microphone or no internet.

* **Local by default** — files, notes, knowledge, reminders and system status work
  with no internet and no third-party packages.
* **Confirmation first** — anything that changes state (files, messages, calls,
  settings, volume, startup) is staged and needs an explicit *yes*.
* **No shell** — JARVIS never runs arbitrary shell commands and never types commands
  into a terminal for you.
* **254 passing local tests**, and they run completely offline.

---

## Contents

1. [What it does](#what-it-does)
2. [Install](#install) — [Windows (PowerShell)](#windows--powershell) ·
   [Windows (cmd)](#windows--command-prompt-cmd) · [Linux](#linux) · [macOS](#macos)
3. [First run](#first-run)
4. [Commands](#commands)
5. [Optional extras](#optional-extras)
6. [Account integrations](#account-integrations)
7. [Configuration](#configuration)
8. [Privacy and safety](#privacy-and-safety)
9. [Troubleshooting](#troubleshooting)
10. [Project layout and tests](#project-layout-and-tests)

---

## What it does

### Voice assistant
* **Wake word** — say “Hey Jarvis” to wake Jarvis. Small mis-hearings (“hey jervis”,
  “ok jarvas”, a bare “jarvis”) still match.
* **Follow-up conversation** — after waking it you can keep giving commands for about
  one minute without repeating the wake phrase. It then returns to standby.
* **Voice replies** — understands spoken requests and replies aloud. Speech
  transcription and general answers use online services.
* **Response-time target** — tuned for a reply in under 4 seconds. This is a target,
  not a guarantee; internet speed and external services can make some replies slower.
  `jarvis --command … --json` reports the measured `elapsed` time.
* **Short-term memory** — remembers recent conversation while it runs. Memory lives in
  RAM only and is cleared when Jarvis exits.

### Screen and apps
* **Ask about the screen** — “what is on my screen”. Capture happens only when
  requested *and* confirmed; the image is sent to an online service for analysis.
* **Apps and websites** — find and open an app, list available apps, or open a website
  (`open github.com`, `open youtube`). URLs are confirmed first.
* **App controls** — JARVIS can inspect and drive controls only in the small set of
  apps that expose them; support varies, and some apps expose nothing. Actions that
  change state require confirmation.
* **No arbitrary shell commands** — ever.

### Local commands
* **Computer status** — memory, battery, CPU, free disk space, uptime.
* **Files** — list, search, read or create supported text files in Jarvis’s own
  `files` folder. Existing files are never overwritten; path traversal is refused.
* **Reminders** — add or list reminders. Alerts work only while Jarvis is running and
  the computer is on.
* **Notes and knowledge** — save notes locally and search everything you saved.
* **Offline console** — every local command works as text, with no microphone and no
  cloud services (a truly offline mode).

### Offline work
Local console commands, notes, files and saved information work without internet.
Full voice conversations, online research, Gmail, WhatsApp, SMS/calls **and** voice
transcription/spoken replies need internet access. Full offline voice conversation is
not currently available.

### Startup and background listening
* Jarvis can be configured to start **visibly** at sign-in. Startup is optional and is
  never installed automatically.
* While running and while the machine is on and awake, it can listen locally for
  “Hey Jarvis” in standby.
* A computer in real Windows Sleep, or powered off, cannot listen. Jarvis starts after
  you power on and sign in only if you enabled the optional visible startup launcher.

### Camera gestures
* “activate gesture mode” opens the visible camera preview; “deactivate gesture mode”
  closes it.
* **Camera processing is local** — frames are not saved and not uploaded.
* A gesture must stay stable for the dwell gate (`1.2 s` by default) before it acts:

  | Gesture | Effect |
  |---|---|
  | Open palm | pause gesture recognition (“resume gesture recognition” to continue) |
  | Fist | cancel a pending action |
  | Thumbs-up | confirm an action that is already waiting for confirmation |

* A gesture **cannot** start a message or a call by itself.
* Camera accuracy and performance still need testing on your device.

### Web research
* Search the web only when you explicitly ask, and get a summary **with citations**.
* Research is **not** saved automatically — say “save this to knowledge” (or use
  `KnowledgeBase.save_last_research()`) to store a result locally.

### Optional account integrations
Implemented in the project, but each needs your own account setup — see
[INTEGRATIONS.md](INTEGRATIONS.md).

* **Gmail** — check unread messages with Google authorisation. **Read-only**: Jarvis
  never sends or deletes mail.
* **WhatsApp** — send messages through Meta’s official WhatsApp Cloud API. Receiving
  incoming messages needs a Meta webhook and a reachable HTTPS endpoint.
* **SMS and calls** — send SMS or place outbound calls through Twilio. These actions
  may incur charges.
* Messages and calls need a separate confirmation. A thumbs-up can confirm a pending
  action but **cannot create** one.

### Windows and device features
* Open selected Windows Settings pages and adjust volume — with confirmation.
* Scan for nearby Bluetooth LE devices. Pairing and connecting are **not** implemented.
* Optionally add or remove a visible Windows Startup launcher. Jarvis does not install
  itself as a hidden background service.

---

## Install

**Requirement:** Python **3.9+**. Check with `python --version` (Windows) or
`python3 --version` (Linux/macOS).

JARVIS has **no required third-party dependency** — the offline console, files, notes,
knowledge, reminders and system status run on a bare Python install. Extras are opt-in.

> Every command below is safe to copy and paste. If an optional extra fails to build
> (usually OpenCV/MediaPipe on an old machine), the installers fall back to the core
> package automatically.

### Windows — PowerShell

```powershell
# 1. Get the code
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis

# 2. Run the installer (creates .venv, installs extras, runs tests, self-check)
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1

#    Prefer a smaller install? Choose the extras you want:
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Extras voice
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Extras none

# 3. Activate the environment
.\.venv\Scripts\Activate.ps1

# 4. Run it
jarvis --console
```

If the activation script is blocked (“running scripts is disabled”), allow local
scripts once and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Manual equivalent if you would rather not use the script:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[all]"
.\.venv\Scripts\python.exe -m jarvis --doctor
```

### Windows — Command Prompt (cmd)

```cmd
REM 1. Get the code
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis

REM 2. Run the installer wrapper (it calls the PowerShell script for you)
install-windows.cmd

REM    Or pick a smaller install:
install-windows.cmd voice
install-windows.cmd none

REM 3. Activate the environment
.venv\Scripts\activate.bat

REM 4. Run it
jarvis --console
```

Manual equivalent in cmd:

```cmd
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[all]"
.venv\Scripts\python.exe -m jarvis --doctor
```

No Python yet? `winget install --id Python.Python.3.12 -e` (or install from
python.org and tick **“Add python.exe to PATH”**).

### Linux

```bash
# 1. System packages (Debian/Ubuntu shown; see below for Fedora and Arch)
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

#    Microphone + camera extras also want these:
sudo apt install -y python3-dev portaudio19-dev libgl1 libglib2.0-0

# 2. Get the code and install
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis
sh install-unix.sh              # all extras; use "none" for core only

# 3. Activate
. .venv/bin/activate

# 4. Run it
jarvis --console
```

Other distributions:

```bash
# Fedora
sudo dnf install -y python3 python3-pip python3-devel portaudio-devel git
# Arch
sudo pacman -S --needed python python-pip git portaudio
# Bluetooth scanning only
sudo systemctl enable --now bluetooth
```

Manual equivalent:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
python -m jarvis --doctor
```

> Headless server? Use `python -m jarvis --console` — no microphone and no display
> required.

### macOS

```bash
# 1. Python (system python3 works if it is 3.9+)
brew install python@3.12 portaudio   # optional, portaudio is for the voice extra
xcode-select --install               # if pip ever needs a compiler

# 2. Get the code and install
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis
sh install-unix.sh

# 3. Activate
. .venv/bin/activate

# 4. Run it
jarvis --console
```

Manual equivalent:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
python -m jarvis --doctor
```

Grant **Microphone** and **Screen Recording** permission to your terminal application
in **System Settings → Privacy & Security** the first time you use voice or screen
features. Apple-silicon Macs: if OpenCV/MediaPipe fail to install, use
`sh install-unix.sh voice` and add `vision` later — gesture mode is optional.

### Verify any install

```bash
jarvis --version            # JARVIS 0.2.0
jarvis --doctor             # capabilities + integration status as JSON
python -m pytest -q         # 254 passing tests, fully offline
```

Full step-by-step notes, including what to do when something fails, live in
[INSTALL.md](INSTALL.md).

---

## First run

```bash
jarvis --console
```

```text
JARVIS v0.2 — offline console
Type a command, or "help" for the list. "exit" leaves the console.

you> system status
jarvis> I am running on Linux 6.12.9 (x86_64), host studio, using Python 3.12.3.
        Memory: 6.1 GB used of 15.5 GB (39% in use), 9.4 GB available.
        ...

you> create file todo.txt with buy milk
jarvis> Confirm and I will create the file todo.txt in the Jarvis files folder. Say yes or no.

you> yes
jarvis> Created todo.txt in /home/you/.local/share/jarvis/files.
```

Useful entry points:

| Command | What it does |
|---|---|
| `jarvis --console` | Offline text console (default, no microphone needed) |
| `jarvis --voice` | Standby listening for “Hey Jarvis” |
| `jarvis --tui` | Full-screen terminal UI (`tui` extra) |
| `jarvis --command "system status"` | One request, then exit |
| `jarvis --command "open github.com" --yes` | Auto-confirm the staged action |
| `jarvis --doctor` | Capability and integration self-check (JSON) |
| `jarvis --init-config` | Write a starter `config.json` |
| `jarvis --print-config-path` | Where `config.json` lives |

Voice mode needs the `voice` extra, a microphone and `OPENAI_API_KEY` for online
transcription. Without them, `jarvis --voice` explains why and drops into the console.

---

## Commands

Anything below can be typed in the console or spoken after the wake word. The wake
phrase and politeness prefixes (“hey jarvis”, “can you”, “please”) are optional.

### Conversation
| Say | Result |
|---|---|
| `help` | full command list |
| `what time is it` | current time and date |
| `who are you` | short self-description |
| `go to sleep` | back to standby / leave the loop |
| `yes` / `confirm` | run the action waiting for confirmation |
| `no` / `cancel` | discard it |

### Computer status
`system status`, `how much memory is free`, `battery status`, `cpu usage`,
`free disk space`, `which os is this`, `how long has this computer been on`.

### Files (inside `<data>/files`)
`list files`, `search files for notes`, `read file todo.txt`,
`create file todo.txt with buy milk` *(asks first, never overwrites)*.

### Notes and knowledge
`save a note buy milk`, `list notes`, `search notes for milk`,
`search knowledge for batteries`, `save this to knowledge`.

### Reminders
`remind me to stretch in 10 minutes`, `remind me to call mum in 2 hours`,
`list reminders`, `clear reminders` *(asks first)*.

### Apps, screen, web
`list apps`, `open notepad`, `open calculator`, `open github.com` *(asks first)*,
`what is on my screen` *(asks first)*, `research solid state batteries`.

### Gestures and Windows/device
`activate gesture mode`, `deactivate gesture mode`, `pause gesture recognition`,
`resume gesture recognition`, `open bluetooth settings`, `set volume to 30`,
`mute`, `scan for bluetooth devices`, `enable startup`, `disable startup`,
`startup status`.

### Accounts (after setup)
`check my gmail`, `send a whatsapp message to +254700000000 saying I am on my way`,
`send sms to +254700000000 saying hello`, `call +254700000000`.

Anything that is not a local skill goes to the configured language model when a key is
set, and otherwise gets a clear “here is what I can do offline” answer.

---

## Optional extras

```bash
pip install -e ".[voice]"      # sounddevice, numpy, pyttsx3, vosk
pip install -e ".[vision]"     # pillow, opencv-python, mediapipe
pip install -e ".[bluetooth]"  # bleak
pip install -e ".[tui]"        # prompt-toolkit
pip install -e ".[system]"     # psutil
pip install -e ".[all]"        # everything above
pip install -e ".[dev]"        # pytest, pytest-cov, ruff
```

| Extra | Unlocks | Without it |
|---|---|---|
| `voice` | microphone capture, offline speech output (`pyttsx3`), local wake-word model (`vosk`) | text-only replies, console still works |
| `vision` | screen capture + cloud analysis, camera gesture mode | “what is on my screen” explains what is missing |
| `bluetooth` | read-only BLE device scan | scan reports the missing package |
| `system` | exact battery/CPU/memory (uses `/proc`, `sysctl`, Win32 otherwise) | basic readings still work |
| `tui` | full-screen console | line console instead |

---

## Account integrations

All optional, all off until you configure them. Step-by-step instructions:
**[INTEGRATIONS.md](INTEGRATIONS.md)**.

| Integration | Variables | Notes |
|---|---|---|
| Online answers / STT / vision / speech | `OPENAI_API_KEY` (or `GEMINI_API_KEY`) | transcription, general answers, screen analysis, narration |
| Gmail (read-only) | `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` | `python -m jarvis.integrations.gmail_auth` gets the refresh token |
| WhatsApp Cloud API | `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | outbound only; inbound needs a webhook |
| Twilio SMS / calls | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, optional `TWILIO_TO_NUMBER` | may incur charges |

`jarvis --doctor` tells you which of these are currently configured.

---

## Configuration

`config.json` lives in the user data folder:

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\Jarvis` |
| macOS | `~/Library/Application Support/Jarvis` |
| Linux | `$XDG_DATA_HOME/jarvis` (default `~/.local/share/jarvis`) |

Set `JARVIS_HOME` to move it anywhere (handy for a portable copy or for tests).

```bash
jarvis --print-config-path
jarvis --init-config
```

Precedence: built-in defaults → `config.json` → environment variables.

| Key | Env var | Default | Meaning |
|---|---|---|---|
| `assistant_name` | `JARVIS_ASSISTANT_NAME` | `Jarvis` | spoken name |
| `wake_word` | `JARVIS_WAKE_WORD` | `hey jarvis` | wake phrase |
| `follow_up_seconds` | `JARVIS_FOLLOW_UP_SECONDS` | `60` | follow-up window |
| `response_target_seconds` | `JARVIS_RESPONSE_TARGET_SECONDS` | `4` | latency target |
| `memory_turns` | `JARVIS_MEMORY_TURNS` | `20` | short-term memory size |
| `require_confirmation` | `JARVIS_REQUIRE_CONFIRMATION` | `true` | confirm state changes |
| `screen_capture_confirmation` | `JARVIS_SCREEN_CONFIRMATION` | `true` | confirm each capture |
| `cloud_answers` | `JARVIS_CLOUD_ANSWERS` | `true` | allow online answers |
| `research_enabled` | `JARVIS_RESEARCH` | `true` | allow web research |
| `tts_backend` | `JARVIS_TTS` | `auto` | `auto`/`cloud`/`local`/`off` |
| `stt_backend` | `JARVIS_STT` | `auto` | `auto`/`cloud`/`local`/`off` |
| `gestures_enabled` | `JARVIS_GESTURES` | `true` | allow gesture mode |
| `gesture_dwell_seconds` | `JARVIS_GESTURE_DWELL_SECONDS` | `1.2` | dwell gate |
| `startup_enabled` | `JARVIS_STARTUP` | `false` | recorded preference |
| `log_level` | `JARVIS_LOG_LEVEL` | `INFO` | log verbosity |

Set `JARVIS_OFFLINE=1` to refuse all outbound network calls (research and account
features then explain that they need internet).

---

## Privacy and safety

* **No shell.** A guard rejects shell-like requests (`rm -rf`, `sudo`, `powershell -c`,
  `chmod`, `eval(`, pipes into a command…) and says why. Opening a terminal is allowed;
  scripting it is not.
* **Files stay in their folder.** Path traversal, absolute paths and non-text
  extensions are refused. Existing files are never overwritten.
* **Confirmation gates.** Files, URLs, screen capture, settings, volume, startup,
  messages and calls are staged and executed only after *yes*. A gesture can confirm a
  pending action but cannot create one.
* **Camera is local.** Gesture frames are processed in-process and never written to
  disk or uploaded.
* **Audit log.** `logs/audit.jsonl` records requests and action outcomes, with
  credentials redacted (`Bearer …`, `api_key=…`, `sk-…`, Twilio/Meta token shapes).
* **Secrets are never logged.** Environment variables are read at call time and only
  ever appear in requests to their provider.
* **Memory is RAM-only.** Short-term conversation memory is never persisted.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `'python' is not recognized` (Windows) | Install Python from python.org with “Add python.exe to PATH”, or use `py -3` |
| `running scripts is disabled` (PowerShell) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `No module named venv` (Debian/Ubuntu) | `sudo apt install -y python3-venv` |
| `portaudio` / `sounddevice` build error | `sudo apt install portaudio19-dev python3-dev` (Linux), `brew install portaudio` (macOS) |
| `opencv`/`mediapipe` will not install | Skip `vision`: `sh install-unix.sh voice` or `-Extras voice`. Gesture mode stays off, everything else works |
| `jarvis: command not found` after install | Activate the environment first, or run `python -m jarvis …` |
| Microphone hears nothing | Check OS input device and permissions; voice mode falls back to the console |
| Voice mode says transcription needs a key | Set `OPENAI_API_KEY` (transcription is an online service) |
| Screen analysis says a key is missing | Set `OPENAI_API_KEY` or `JARVIS_VISION_API_KEY` |
| Gmail/WhatsApp/Twilio “not configured” | Follow [INTEGRATIONS.md](INTEGRATIONS.md), then `jarvis --doctor` |
| Interrupted replies on a slow link | Expected: the 4-second target is best effort |
| `pip` behind a proxy | `pip install --proxy http://user:pass@host:port -e ".[all]"` |

Run `jarvis --doctor` first — it reports exactly which capability or integration is
missing.

---

## Project layout and tests

```text
jarvis/
  cli.py            command line, --doctor, --console, --voice, --command
  console.py        offline text console
  engine.py         intent router, confirmations, gesture events
  config.py         config loading + validation (file + env)
  memory.py         short-term RAM-only conversation memory
  security.py       shell guard, secret redaction, audit log
  storage.py        atomic JSON persistence
  voice.py          wake word, follow-up window, recording, speech
  wake.py           standby loop
  vision.py         screen capture + cloud analysis
  gestures.py       dwell gate + local camera preview
  research.py       web search with citations
  cloud.py          online LLM, STT, TTS and vision calls (stdlib only)
  tui.py            optional full-screen console
  features/         files, notes, reminders, knowledge, system_info, apps,
                    windows_control, bluetooth, startup
  integrations/     gmail, gmail_auth, whatsapp, twilio_client
tests/              17 test modules, 254 tests, no network required
install-windows.ps1 / install-windows.cmd / install-unix.sh
INTEGRATIONS.md     Gmail, WhatsApp and Twilio setup
INSTALL.md          detailed per-platform installation
```

```bash
python -m pytest -q               # 254 passed
python -m pytest -q --cov=jarvis  # coverage (needs the dev extra)
ruff check .                      # lint (needs the dev extra)
```

**Testing status.** The current workspace has **254 passing local tests**. They do not
verify live Gmail, Meta, Twilio, camera or Windows-device behaviour — those paths need
your accounts and hardware. The integration tests build the real request payloads
against a stubbed HTTP layer, so authentication, validation and error handling are
covered without touching the network.

## License

MIT — see [LICENSE](LICENSE).

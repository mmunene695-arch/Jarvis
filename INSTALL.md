# Installing JARVIS v0.2

JARVIS runs on **Windows 10/11, Linux and macOS** with **Python 3.9 or newer**.

There is **nothing you must `pip install`** for the core assistant to work. The offline
console, files, notes, knowledge, reminders and system status use only the Python
standard library. Optional extras add the microphone, camera, Bluetooth and terminal UI.

Pick your platform:

* [0. Check Python](#0-check-python)
* [1. Windows — PowerShell](#1-windows--powershell)
* [2. Windows — Command Prompt (cmd)](#2-windows--command-prompt-cmd)
* [3. Linux](#3-linux)
* [4. macOS](#4-macos)
* [5. Verify the install](#5-verify-the-install)
* [6. Optional extras](#6-optional-extras)
* [7. Removing JARVIS](#7-removing-jarvis)
* [8. Troubleshooting](#8-troubleshooting)

---

## 0. Check Python

**Windows (PowerShell or cmd)**

```powershell
py -3 --version
python --version
```

**Linux / macOS**

```bash
python3 --version
```

You need `Python 3.9.x` or newer. If the command is missing:

| OS | Install |
|---|---|
| Windows | `winget install --id Python.Python.3.12 -e` or <https://www.python.org/downloads/windows/> (tick **“Add python.exe to PATH”**) |
| Debian/Ubuntu | `sudo apt update && sudo apt install -y python3 python3-venv python3-pip git` |
| Fedora | `sudo dnf install -y python3 python3-pip git` |
| Arch | `sudo pacman -S --needed python python-pip git` |
| macOS | `brew install python@3.12` or <https://www.python.org/downloads/macos/> |

Also install `git` if you want to clone the repository; otherwise download the ZIP from
<https://github.com/mmunene695-arch/Jarvis/archive/refs/heads/main.zip> and extract it.

---

## 1. Windows — PowerShell

Run these in **PowerShell** (Start menu → “PowerShell”). A normal user account is
enough; no administrator rights are needed for a per-user install.

```powershell
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis

# Installer: creates .venv, installs JARVIS + extras, runs the tests, self-check
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1

# Activate the environment in this terminal
.\.venv\Scripts\Activate.ps1

# Run
jarvis --console
```

Installer options:

```powershell
.\install-windows.ps1 -Extras all        # default: every optional extra
.\install-windows.ps1 -Extras voice      # microphone + offline speech + local wake word
.\install-windows.ps1 -Extras none       # core only, zero third-party packages
.\install-windows.ps1 -NoVenv            # install into the current Python environment
.\install-windows.ps1 -VenvDir C:\Tools\jarvis-venv
.\install-windows.ps1 -SkipTests
```

If PowerShell refuses to run the activation script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Manual install (Windows / PowerShell)

```powershell
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[all]"     # or -e "." for core only
.\.venv\Scripts\python.exe -m jarvis --doctor
```

### Optional: visible startup launcher

JARVIS never installs itself as a hidden service. If you want it to start **visibly**
when you sign in:

```powershell
jarvis --command "enable startup" --yes
jarvis --command "startup status"
jarvis --command "disable startup" --yes   # remove it again
```

That writes `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\JARVIS.lnk.start.cmd`.
Delete the file at any time.

---

## 2. Windows — Command Prompt (cmd)

Open **cmd** (Start menu → “Command Prompt”).

```bat
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis

REM Wrapper that runs the PowerShell installer for you
install-windows.cmd

REM Or choose extras:  install-windows.cmd voice   /   install-windows.cmd none

REM Activate
.venv\Scripts\activate.bat

REM Run
jarvis --console
```

### Manual install (Windows / cmd)

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[all]"
.venv\Scripts\python.exe -m jarvis --doctor
```

Leave the environment with `deactivate`. To run outside an activated prompt, use the
full path: `.venv\Scripts\jarvis.exe --console`.

> **cmd tip:** in `cmd`, quote the extras: `pip install -e ".[voice]"`. Unquoted square
> brackets are not special in `cmd`, but quoting avoids surprises in PowerShell.

---

## 3. Linux

```bash
# System prerequisites (Debian/Ubuntu)
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

# Optional, only for the voice/vision extras
sudo apt install -y python3-dev portaudio19-dev libgl1 libglib2.0-0

# Install
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis
sh install-unix.sh            # or: sh install-unix.sh none   /   sh install-unix.sh voice

# Activate and run
. .venv/bin/activate
jarvis --console
```

Other distributions:

```bash
# Fedora
sudo dnf install -y python3 python3-pip python3-devel portaudio-devel git

# Arch
sudo pacman -S --needed python python-pip git portaudio

# Bluetooth LE scanning needs the service running
sudo systemctl enable --now bluetooth
```

Installer options (environment variables):

```bash
VENV_DIR=~/venvs/jarvis sh install-unix.sh        # custom venv location
NO_VENV=1 sh install-unix.sh                      # install into the current environment
SKIP_TESTS=1 sh install-unix.sh                   # skip the pytest run
```

### Manual install (Linux)

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
python -m jarvis --doctor
```

**Headless machine / SSH session:** use `python -m jarvis --console`. Microphone,
camera and screen features need a graphical desktop session; everything else works.

---

## 4. macOS

```bash
# Prerequisites (Homebrew optional; system python3 works if it is 3.9+)
xcode-select --install          # only if pip later needs a compiler
brew install python@3.12 portaudio

# Install
git clone https://github.com/mmunene695-arch/Jarvis.git
cd Jarvis
sh install-unix.sh

# Activate and run
. .venv/bin/activate
jarvis --console
```

**Permissions.** The first time you use the microphone or screen capture, macOS asks for
access. Grant it to your **terminal app** (Terminal, iTerm, VS Code):

* **System Settings → Privacy & Security → Microphone**
* **System Settings → Privacy & Security → Screen Recording**
* **System Settings → Privacy & Security → Camera** (gesture mode)

Restart the terminal after changing these.

**Apple silicon note.** If `opencv-python` or `mediapipe` fail to install, use a smaller
extra and add vision later:

```bash
sh install-unix.sh voice        # microphone + offline speech only
```

### Manual install (macOS)

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
python -m jarvis --doctor
```

---

## 5. Verify the install

Run all three, in an activated environment:

```bash
jarvis --version        # JARVIS 0.2.0
jarvis --doctor         # JSON report of capabilities and integrations
python -m pytest -q     # 254 passed (fully offline)
```

`--doctor` output example (abridged):

```json
{
  "version": "0.2.0",
  "platform": { "system": "Windows", "release": "11", "python": "3.12.4" },
  "capabilities": {
    "microphone": true,
    "local_tts": true,
    "cloud_llm": false,
    "screen_capture": false,
    "gesture_mode": false
  },
  "integrations": { "gmail": false, "whatsapp": false, "twilio": false }
}
```

A `false` value is not an error — it means that optional piece is not set up yet.

Quick functional check:

```bash
jarvis --command "system status"
jarvis --command "save a note instal works"
jarvis --command "list notes"
```

---

## 6. Optional extras

```bash
pip install -e ".[voice]"      # sounddevice, numpy, pyttsx3, vosk
pip install -e ".[vision]"     # pillow (screen), opencv-python + mediapipe (gestures)
pip install -e ".[bluetooth]"  # bleak
pip install -e ".[tui]"        # prompt-toolkit
pip install -e ".[system]"     # psutil
pip install -e ".[all]"        # everything above
pip install -e ".[dev]"        # pytest, pytest-cov, ruff
```

Then set the keys you need — see [INTEGRATIONS.md](INTEGRATIONS.md). For a normal
voice setup:

```powershell
# Windows PowerShell (persist for your user; open a new terminal afterwards)
setx OPENAI_API_KEY "sk-..."
```
```bash
# Linux / macOS
export OPENAI_API_KEY="sk-..."
```

`jarvis --doctor` confirms each capability afterwards.

---

## 7. Removing JARVIS

```bash
# 1. Disable the optional startup launcher, if you enabled it
jarvis --command "disable startup" --yes

# 2. Remove the virtual environment and the cloned folder
#    Windows
rmdir /s /q .venv
#    Linux / macOS
rm -rf .venv
```

Your data folder (notes, files, logs) is separate — delete it if you want a clean slate:

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\Jarvis` |
| macOS | `~/Library/Application Support/Jarvis` |
| Linux | `~/.local/share/jarvis` |

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `'python' is not recognized` | Python not on PATH | reinstall with “Add python.exe to PATH”, or use `py -3` |
| `'jarvis' is not recognized` | environment not activated | `.\.venv\Scripts\Activate.ps1` (PS) / `.venv\Scripts\activate.bat` (cmd) / `pip show jarvis-assistant` |
| `running scripts is disabled on this system` | PowerShell policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `No module named venv` | Debian splits venv out | `sudo apt install -y python3-venv` |
| `Failed building wheel for sounddevice` | missing PortAudio headers | `sudo apt install portaudio19-dev python3-dev` / `brew install portaudio` |
| `Failed building wheel for mediapipe` or OpenCV | old interpreter/CPU | `pip install -e ".[voice]"` and skip gestures |
| `Could not build wheels for numpy` | very old pip | `python -m pip install --upgrade pip` |
| `externally-managed-environment` (PEP 668) | installing outside a venv on newer distros | use the virtual environment from this guide, or `pip install --user` |
| Microphone silently does nothing | OS permission/device | check OS input settings, then `jarvis --doctor` |
| Voice mode says transcription needs a key | online STT | set `OPENAI_API_KEY`; use `--console` otherwise |
| `jarvis --voice` drops to the console | `sounddevice` or key missing | see the printed reason; that fallback is intentional |
| Screen analysis reports a missing key | no vision key | set `OPENAI_API_KEY` or `JARVIS_VISION_API_KEY` |
| Gesture mode reports missing packages | OpenCV/MediaPipe absent | `pip install -e ".[vision]"` |
| Bluetooth scan fails on Linux | service off / no adapter | `sudo systemctl enable --now bluetooth`; requires an adapter |
| Gmail / WhatsApp / Twilio “not configured” | account setup missing | [INTEGRATIONS.md](INTEGRATIONS.md), then `jarvis --doctor` |
| Replies slower than 4 seconds | network/provider latency | target only; `--json` shows measured time |
| pip behind a proxy | corporate network | `pip install --proxy http://user:pass@host:port -e ".[all]"` |

Still stuck? Run `jarvis --doctor` and check `<data folder>/logs/audit.jsonl` — secrets
are redacted, so it is safe to share.

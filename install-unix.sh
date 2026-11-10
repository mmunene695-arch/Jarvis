#!/usr/bin/env sh
# JARVIS v0.2 installer for Linux and macOS.
#
# Usage:
#   sh install-unix.sh                 # all optional extras
#   sh install-unix.sh voice           # one extra set
#   sh install-unix.sh none            # core only (no third-party packages)
#   NO_VENV=1 sh install-unix.sh       # install into the current environment
set -eu

EXTRAS="${1:-all}"
VENV_DIR="${VENV_DIR:-.venv}"
NO_VENV="${NO_VENV:-0}"
SKIP_TESTS="${SKIP_TESTS:-0}"

step() { printf '\n==> %s\n' "$1"; }
ok()   { printf '    [ok] %s\n' "$1"; }
warn() { printf '    [!]  %s\n' "$1"; }
die()  { printf '\n%s\n' "$1" >&2; exit 1; }

printf 'JARVIS v0.2 installer (%s)\n' "$(uname -s 2>/dev/null || echo unknown)"
printf 'Python 3.9 or newer is required.\n'

step "Looking for Python"
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
        major="$(printf '%s' "$version" | cut -d. -f1)"
        minor="$(printf '%s' "$version" | cut -d. -f2)"
        if [ "${major:-0}" = "3" ] && [ "${minor:-0}" -ge 9 ] 2>/dev/null; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    printf '\nNo suitable Python found. Install Python 3.9+:\n'
    printf '  Debian/Ubuntu : sudo apt update && sudo apt install -y python3 python3-venv python3-pip\n'
    printf '  Fedora        : sudo dnf install -y python3 python3-pip\n'
    printf '  Arch          : sudo pacman -S --needed python python-pip\n'
    printf '  macOS (brew)  : brew install python@3.12\n'
    exit 1
fi
ok "Python $("$PYTHON" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])') found ($PYTHON)"

if [ "$NO_VENV" = "1" ]; then
    step "Using the current Python environment (NO_VENV=1)"
    RUN="$PYTHON"
else
    if [ ! -d "$VENV_DIR" ]; then
        step "Creating virtual environment in $VENV_DIR"
        "$PYTHON" -m venv "$VENV_DIR" || die "Could not create a virtual environment.
On Debian/Ubuntu install the venv module: sudo apt install -y python3-venv"
    else
        step "Reusing virtual environment $VENV_DIR"
    fi
    RUN="$VENV_DIR/bin/python"
    [ -x "$RUN" ] || die "The virtual environment looks incomplete: $RUN is missing."
    ok "Virtual environment ready"
fi

step "Upgrading pip"
"$RUN" -m pip install --upgrade pip --quiet || warn "pip upgrade failed; continuing."

if [ "$EXTRAS" = "none" ]; then
    TARGET="."
else
    TARGET=".[$EXTRAS]"
fi

step "Installing JARVIS ($TARGET)"
if ! "$RUN" -m pip install -e "$TARGET"; then
    warn "Installing every extra failed on this machine."
    printf '    JARVIS itself has no required dependencies; retrying with the core package.\n'
    "$RUN" -m pip install -e "." || die "Installation failed. Check the pip output above."
    ok "Core package installed (optional extras skipped)"
else
    ok "Package installed"
fi

if [ "$SKIP_TESTS" != "1" ]; then
    step "Running the local test suite (offline)"
    "$RUN" -m pip install --quiet pytest || true
    if "$RUN" -m pytest -q; then
        ok "All local tests passed"
    else
        warn "Some tests failed. JARVIS may still work; see the output above."
    fi
fi

step "Self-check"
"$RUN" -m jarvis --doctor || true

printf '\nJARVIS is installed.\n\n'
if [ "$NO_VENV" = "1" ]; then
    printf "The 'jarvis' command should already be on your PATH.\n"
else
    printf 'Activate the environment for this terminal:\n    . %s/bin/activate\n' "$VENV_DIR"
fi
printf '\n'
printf 'Start the offline console (no microphone needed):\n    jarvis --console\n'
printf 'Ask one question and exit:\n    jarvis --command "system status"\n'
printf 'Start voice standby (needs the voice extra and OPENAI_API_KEY):\n    jarvis --voice\n'
printf '\n'
printf 'Linux: if the microphone or camera extras fail to build, install the system packages first:\n'
printf '    sudo apt install -y python3-dev portaudio19-dev libgl1 libglib2.0-0\n'
printf 'macOS: grant Microphone and Screen Recording permission to your terminal app in\n'
printf '    System Settings > Privacy & Security.\n'
printf '\n'

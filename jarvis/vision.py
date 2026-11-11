"""Screen capture and cloud image analysis.

Capture only happens after an explicit, confirmed request. The image is sent to
an online vision model and is not stored on disk.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys

from . import cloud
from .errors import FeatureUnavailable, NetworkError


def pillow_available() -> bool:
    try:
        from PIL import ImageGrab  # noqa: F401

        return True
    except Exception:
        return False


def online_available(env: dict[str, str] | None = None) -> bool:
    """True when a vision-capable key is configured."""
    return cloud.available(env, task="vision")


def available() -> bool:
    """True when a screenshot can be taken and analysed."""
    return pillow_available() and online_available()


def capture_screen(*, max_width: int = 1440) -> bytes:
    """Return a PNG screenshot of the primary screen."""
    if not pillow_available():
        raise FeatureUnavailable(
            'Screen capture needs Pillow. Install it with: pip install "jarvis-assistant[vision]"'
        )
    from PIL import ImageGrab  # type: ignore

    image = None
    try:
        image = ImageGrab.grab()
    except Exception:
        image = None
    if image is None:
        image = _capture_with_tool()
    if image is None:
        raise FeatureUnavailable(
            "I could not capture the screen. On Linux you may need scrot, gnome-screenshot "
            "or imagemagick installed, and a running desktop session."
        )
    if image.width > max_width:
        ratio = max_width / float(image.width)
        image = image.resize((max_width, int(image.height * ratio)))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _capture_with_tool():  # pragma: no cover - depends on installed tools
    """Linux fallbacks that write a temporary PNG and read it back."""
    from PIL import Image

    candidates: list[list[str]] = []
    if sys.platform.startswith("linux"):
        if shutil.which("scrot"):
            candidates.append(["scrot", "-o", "-"])
        if shutil.which("gnome-screenshot"):
            candidates.append(["gnome-screenshot", "-f", "/dev/stdout"])
        if shutil.which("import"):
            candidates.append(["import", "-window", "root", "-"])
    for command in candidates:
        try:
            result = subprocess.run(command, capture_output=True, timeout=10, check=False)
            if result.returncode == 0 and result.stdout:
                return Image.open(io.BytesIO(result.stdout))
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def analyse(image_bytes: bytes, *, prompt: str = "Describe what is on this screen.", env: dict[str, str] | None = None) -> str:
    """Send one screenshot to the vision model and return the description."""
    if not image_bytes:
        raise FeatureUnavailable("There was nothing to analyse.")
    if not cloud.available(env, task="vision"):
        raise NetworkError(
            "Screen analysis needs an online vision key. Set OPENAI_API_KEY or "
            "JARVIS_VISION_API_KEY. See INTEGRATIONS.md."
        )
    return cloud.describe_image(image_bytes, prompt=prompt, env=os.environ if env is None else env)

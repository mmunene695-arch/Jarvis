"""Local camera gesture recognition.

Camera frames are processed on this computer and are never saved or uploaded.
A gesture only acts after it has been held for the dwell gate, so a hand waving
past the camera cannot trigger anything.

Supported gestures: open palm (pause), fist (cancel), thumbs-up (confirm).
A gesture can never *start* a message or call; only an explicit request can.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

OPEN_PALM = "open_palm"
FIST = "fist"
THUMBS_UP = "thumbs_up"
UNKNOWN = "unknown"

_ALIASES = {
    "open palm": OPEN_PALM,
    "open_palm": OPEN_PALM,
    "palm": OPEN_PALM,
    "stop": OPEN_PALM,
    "five": OPEN_PALM,
    "fist": FIST,
    "closed fist": FIST,
    "no": FIST,
    "thumbs up": THUMBS_UP,
    "thumbs_up": THUMBS_UP,
    "thumb up": THUMBS_UP,
    "yes": THUMBS_UP,
    "ok": THUMBS_UP,
}


def canonical(name: str) -> str:
    """Map a spoken or model label to a canonical gesture name."""
    key = (name or "").strip().lower().replace("-", "_")
    if key in _ALIASES:
        return _ALIASES[key]
    normalised = key.replace("_", " ")
    return _ALIASES.get(normalised, UNKNOWN)


def describe_gesture(name: str) -> str:
    return {
        OPEN_PALM: "an open palm pauses gesture recognition",
        FIST: "a fist cancels a pending action",
        THUMBS_UP: "a thumbs-up confirms a pending action",
    }.get(canonical(name), "that gesture is not mapped to an action")


# ----------------------------------------------------------------------
# Dwell gate
# ----------------------------------------------------------------------
@dataclass
class DwellGate:
    """Requires one gesture to be held steadily before it fires.

    ``feed`` is called for every processed frame. It returns the gesture name
    exactly once when the dwell requirement is met, then stays quiet until the
    hand changes (and re-arms after a short cooldown).
    """

    dwell_seconds: float = 1.2
    cooldown_seconds: float = 1.5
    clock: Callable[[], float] = field(default=time.monotonic)
    _current: str = field(default=UNKNOWN, repr=False)
    _since: float = field(default=0.0, repr=False)
    _fired: bool = field(default=False, repr=False)
    _last_fired: float = field(default=float("-inf"), repr=False)

    def __post_init__(self) -> None:
        if self.dwell_seconds <= 0:
            raise ValueError("dwell_seconds must be greater than zero")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must not be negative")

    @property
    def stable_seconds(self) -> float:
        if self._current == UNKNOWN:
            return 0.0
        return max(0.0, self.clock() - self._since)

    def feed(self, gesture: str, now: float | None = None) -> str | None:
        moment = self.clock() if now is None else float(now)
        name = canonical(gesture)
        if name != self._current:
            self._current = name
            self._since = moment
            self._fired = False
            return None
        if name == UNKNOWN or self._fired:
            return None
        if moment - self._since < self.dwell_seconds:
            return None
        if moment - self._last_fired < self.cooldown_seconds:
            return None
        self._fired = True
        self._last_fired = moment
        return name

    def reset(self) -> None:
        self._current = UNKNOWN
        self._since = 0.0
        self._fired = False


# ----------------------------------------------------------------------
# Camera preview process
# ----------------------------------------------------------------------
def available() -> bool:
    try:
        import cv2  # noqa: F401
        import mediapipe  # noqa: F401

        return True
    except Exception:
        return False


@dataclass
class GesturePreview:
    """A visible OpenCV preview window that processes frames locally."""

    on_gesture: Callable[[str], None]
    dwell_seconds: float = 1.2
    camera_index: int = 0
    _thread: threading.Thread | None = field(default=None, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, repr=False)
    _gate: DwellGate = field(default=None, repr=False)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._gate = DwellGate(dwell_seconds=self.dwell_seconds)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="jarvis-gestures", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def _run(self) -> None:  # pragma: no cover - requires a camera
        import cv2
        import mediapipe as mp

        hands = mp.solutions.hands.Hands(
            max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5
        )
        capture = cv2.VideoCapture(self.camera_index)
        if not capture.isOpened():
            self.on_gesture("camera_unavailable")
            return
        try:
            while not self._stop.is_set():
                ok, frame = capture.read()
                if not ok:
                    time.sleep(0.05)
                    continue
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb)
                label = classify(result.multi_hand_landmarks)
                confirmed = self._gate.feed(label)
                _draw_overlay(cv2, frame, label, self._gate.stable_seconds)
                cv2.imshow("JARVIS gesture preview (local only)", frame)
                if confirmed:
                    self.on_gesture(confirmed)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
        finally:
            capture.release()
            hands.close()
            cv2.destroyAllWindows()


def _draw_overlay(cv2, frame, label: str, stable: float) -> None:  # pragma: no cover
    text = f"{label}  {stable:.1f}s"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(
        frame,
        "frames stay on this computer",
        (10, frame.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )


def classify(hand_landmarks) -> str:  # pragma: no cover - needs mediapipe output
    """Classify a MediaPipe hand into open palm, fist or thumbs-up."""
    if not hand_landmarks:
        return UNKNOWN
    landmarks = hand_landmarks.landmark
    fingers = _extended_fingers(landmarks)
    count = sum(fingers.values())
    thumb_up = _thumb_up(landmarks, fingers)
    if count == 0 and not thumb_up:
        return FIST
    if thumb_up and count == 1:
        return THUMBS_UP
    if count >= 4:
        return OPEN_PALM
    return UNKNOWN


def _extended_fingers(landmarks) -> dict[str, bool]:
    tips = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
    return {name: landmarks[tip].y < landmarks[tip - 2].y for name, tip in tips.items()}


def _thumb_up(landmarks, fingers: dict[str, bool]) -> bool:
    thumb_tip, thumb_base = landmarks[4], landmarks[2]
    others_down = not any(fingers.values())
    return others_down and thumb_tip.y < thumb_base.y - 0.05


_active_preview: GesturePreview | None = None


def launch_preview(on_gesture: Callable[[str], None] | None = None, dwell_seconds: float = 1.2) -> bool:
    """Open the visible camera preview. Returns False when OpenCV is missing."""
    global _active_preview
    if not available():
        return False
    if _active_preview is not None and _active_preview.running:
        return True
    _active_preview = GesturePreview(
        on_gesture=on_gesture or (lambda gesture: None), dwell_seconds=dwell_seconds
    )
    _active_preview.start()
    return True


def stop_preview() -> None:
    global _active_preview
    if _active_preview is not None:
        _active_preview.stop()
        _active_preview = None

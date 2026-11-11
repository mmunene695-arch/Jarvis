"""Gesture names, aliases and the dwell gate."""

from __future__ import annotations

import pytest

from jarvis.gestures import (
    FIST,
    OPEN_PALM,
    THUMBS_UP,
    UNKNOWN,
    DwellGate,
    canonical,
)


@pytest.mark.parametrize(
    "label,expected",
    [
        ("open palm", OPEN_PALM),
        ("OPEN_PALM", OPEN_PALM),
        ("palm", OPEN_PALM),
        ("fist", FIST),
        ("closed fist", FIST),
        ("thumbs up", THUMBS_UP),
        ("thumbs-up", THUMBS_UP),
        ("yes", THUMBS_UP),
        ("waving", UNKNOWN),
        ("", UNKNOWN),
    ],
)
def test_canonical_labels(label: str, expected: str):
    assert canonical(label) == expected


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_dwell_gate_requires_stable_hold():
    clock = FakeClock()
    gate = DwellGate(dwell_seconds=1.0, cooldown_seconds=0, clock=clock)
    assert gate.feed(THUMBS_UP) is None
    clock.now = 0.5
    assert gate.feed(THUMBS_UP) is None
    clock.now = 1.05
    assert gate.feed(THUMBS_UP) == THUMBS_UP


def test_dwell_gate_ignores_flicker():
    clock = FakeClock()
    gate = DwellGate(dwell_seconds=1.0, cooldown_seconds=0, clock=clock)
    gate.feed(FIST)
    clock.now = 0.6
    assert gate.feed(None) is None  # hand left the frame
    clock.now = 0.7
    assert gate.feed(FIST) is None  # timer restarted
    clock.now = 1.0
    assert gate.feed(FIST) is None
    clock.now = 1.75
    assert gate.feed(FIST) == FIST


def test_dwell_gate_fires_once_and_cools_down():
    clock = FakeClock()
    gate = DwellGate(dwell_seconds=0.5, cooldown_seconds=2.0, clock=clock)
    gate.feed(OPEN_PALM)
    clock.now = 0.6
    assert gate.feed(OPEN_PALM) == OPEN_PALM
    clock.now = 1.0
    assert gate.feed(OPEN_PALM) is None
    gate.feed(None)
    clock.now = 1.2
    assert gate.feed(OPEN_PALM) is None
    clock.now = 2.6
    assert gate.feed(OPEN_PALM) == OPEN_PALM


def test_unknown_gesture_never_fires():
    clock = FakeClock()
    gate = DwellGate(dwell_seconds=0.1, cooldown_seconds=0, clock=clock)
    gate.feed("hand_wave")
    clock.now = 5
    assert gate.feed("hand_wave") is None


def test_invalid_dwell_config():
    with pytest.raises(ValueError):
        DwellGate(dwell_seconds=0)


def test_stable_seconds_reports_hold_time():
    clock = FakeClock()
    gate = DwellGate(dwell_seconds=1.0, cooldown_seconds=0, clock=clock)
    gate.feed(FIST)
    clock.now = 0.75
    assert gate.stable_seconds == pytest.approx(0.75)
    gate.reset()
    assert gate.stable_seconds == 0.0


def test_available_is_a_boolean():
    from jarvis.gestures import available

    assert isinstance(available(), bool)

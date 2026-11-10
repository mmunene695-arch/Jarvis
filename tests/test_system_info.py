"""System information reporting must never raise, on any platform."""

from __future__ import annotations

import platform

from jarvis.features import system_info


def test_platform_report_mentions_system():
    text = system_info.platform_report()
    assert platform.system() in text


def test_memory_report_is_text():
    text = system_info.memory_report()
    assert isinstance(text, str) and text
    assert "Memory" in text or "could not" in text


def test_battery_report_is_text():
    text = system_info.battery_report()
    assert isinstance(text, str) and text


def test_cpu_report_is_text():
    text = system_info.cpu_report()
    assert "CPU" in text


def test_disk_report_is_text():
    text = system_info.disk_report()
    assert "Disk" in text or "could not" in text


def test_full_report_contains_sections():
    report = system_info.full_report()
    for fragment in ("CPU", "Disk"):
        assert fragment in report


def test_uptime_report_is_text():
    assert isinstance(system_info.uptime_report(), str)


def test_human_bytes():
    assert system_info._human_bytes(512) == "512 B"
    assert system_info._human_bytes(2048) == "2.0 KB"
    assert system_info._human_bytes(5 * 1024**3) == "5.0 GB"

"""Cross-platform system information gathered from /proc, sysctl or psutil."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import Any

_WINDOWS = sys.platform.startswith("win")


def _run(cmd: list[str], timeout: float = 3.0) -> str:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return (out.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _human_bytes(value: float) -> str:
    value = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


# ----------------------------------------------------------------------
# Memory
# ----------------------------------------------------------------------
def memory_info() -> dict[str, Any]:
    """Return total/available memory in bytes (best effort)."""
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        return {"total": int(vm.total), "available": int(vm.available), "percent": float(vm.percent)}
    except Exception:
        pass
    if sys.platform.startswith("linux"):
        try:
            values: dict[str, int] = {}
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    key, _, rest = line.partition(":")
                    if key in {"MemTotal", "MemAvailable"}:
                        values[key] = int(rest.strip().split()[0]) * 1024
            total = values.get("MemTotal", 0)
            available = values.get("MemAvailable", values.get("MemFree", 0))
            percent = (1 - available / total) * 100 if total else 0.0
            return {"total": total, "available": available, "percent": percent}
        except (OSError, ValueError):
            pass
    if sys.platform == "darwin":
        total = 0
        try:
            out = _run(["sysctl", "-n", "hw.memsize"])
            total = int(out or 0)
        except ValueError:
            total = 0
        return {"total": total, "available": 0, "percent": 0.0, "note": "available memory is not reported on macOS without psutil"}
    if _WINDOWS:
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return {
                    "total": int(stat.ullTotalPhys),
                    "available": int(stat.ullAvailPhys),
                    "percent": float(stat.dwMemoryLoad),
                }
        except Exception:
            pass
    return {"total": 0, "available": 0, "percent": 0.0, "note": "memory information unavailable"}


def memory_report() -> str:
    info = memory_info()
    if not info.get("total"):
        return "I could not read the memory information on this system. Installing psutil helps."
    used = info["total"] - info["available"]
    return (
        f"Memory: {_human_bytes(used)} used of {_human_bytes(info['total'])} "
        f"({info.get('percent', 0):.0f}% in use), {_human_bytes(info['available'])} available."
    )


# ----------------------------------------------------------------------
# Battery
# ----------------------------------------------------------------------
def battery_info() -> dict[str, Any]:
    try:
        import psutil  # type: ignore

        battery = psutil.sensors_battery()
        if battery is None:
            return {"present": False}
        secs = battery.secsleft
        return {
            "present": True,
            "percent": float(battery.percent),
            "plugged": bool(battery.power_plugged),
            "seconds_left": None if secs in (None, -1, -2) else int(secs),
        }
    except Exception:
        pass
    if sys.platform.startswith("linux"):
        base = "/sys/class/power_supply"
        try:
            for name in sorted(os.listdir(base)):
                if not name.startswith("BAT"):
                    continue
                with open(f"{base}/{name}/capacity", encoding="utf-8") as handle:
                    percent = float(handle.read().strip())
                status = ""
                try:
                    with open(f"{base}/{name}/status", encoding="utf-8") as handle:
                        status = handle.read().strip().lower()
                except OSError:
                    status = ""
                return {"present": True, "percent": percent, "plugged": status == "charging"}
        except (OSError, ValueError):
            return {"present": False}
    if sys.platform == "darwin":
        out = _run(["pmset", "-g", "batt"])
        if out:
            import re

            percent = re.search(r"(\d+)%", out)
            return {
                "present": percent is not None,
                "percent": float(percent.group(1)) if percent else 0.0,
                "plugged": "AC Power" in out,
            }
    return {"present": False}


def battery_report() -> str:
    info = battery_info()
    if not info.get("present"):
        return "No battery detected, so this machine is probably on mains power."
    state = "charging" if info.get("plugged") else "on battery"
    text = f"Battery is at {info.get('percent', 0):.0f}% and {state}."
    if info.get("seconds_left"):
        minutes = int(info["seconds_left"] // 60)
        text += f" About {minutes} minutes remaining."
    return text


# ----------------------------------------------------------------------
# CPU
# ----------------------------------------------------------------------
def cpu_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "model": platform.processor() or platform.machine() or "unknown",
        "cores": os.cpu_count() or 1,
    }
    try:
        import psutil  # type: ignore

        info["percent"] = float(psutil.cpu_percent(interval=0.25))
        freq = getattr(psutil, "cpu_freq", None)
        if callable(freq):
            f = freq()
            if f:
                info["mhz"] = round(float(getattr(f, "current", 0) or 0), 0)
    except Exception:
        info["percent"] = None
    return info


def cpu_report() -> str:
    info = cpu_info()
    cores = info.get("cores", 1)
    parts = [f"CPU: {info.get('model', 'unknown')} with {cores} logical core{'s' if cores != 1 else ''}."]
    if info.get("percent") is not None:
        parts.append(f"Current load is {info['percent']:.0f}%.")
    return " ".join(parts)


# ----------------------------------------------------------------------
# Disk
# ----------------------------------------------------------------------
def disk_info(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    target = str(path) if path else (os.environ.get("SystemDrive", "C:\\") if _WINDOWS else "/")
    try:
        usage = shutil.disk_usage(target)
        return {
            "path": target,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": (usage.used / usage.total * 100) if usage.total else 0.0,
        }
    except OSError:
        return {"path": target, "total": 0, "used": 0, "free": 0, "percent": 0.0}


def disk_report() -> str:
    info = disk_info()
    if not info["total"]:
        return "I could not read the free disk space."
    return (
        f"Disk {info['path']}: {_human_bytes(info['free'])} free of {_human_bytes(info['total'])} "
        f"({info['percent']:.0f}% used)."
    )


# ----------------------------------------------------------------------
# Platform / uptime
# ----------------------------------------------------------------------
def platform_info() -> dict[str, Any]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "hostname": platform.node(),
    }


def platform_report() -> str:
    info = platform_info()
    return (
        f"I am running on {info['system']} {info['release']} ({info['machine']}), "
        f"host {info['hostname']}, using Python {info['python']}."
    )


def full_report() -> str:
    return "\n".join(
        [
            platform_report(),
            memory_report(),
            battery_report(),
            cpu_report(),
            disk_report(),
        ]
    )

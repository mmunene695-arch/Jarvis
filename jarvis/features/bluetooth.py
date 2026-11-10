"""Bluetooth LE scanning.

Scanning is read-only. Pairing and connecting are intentionally not implemented.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass

from ..errors import FeatureUnavailable, NotSupportedError


@dataclass(frozen=True)
class BleDevice:
    address: str
    name: str
    rssi: int | None = None

    def describe(self) -> str:
        signal = f", signal {self.rssi} dBm" if self.rssi is not None else ""
        return f"• {self.name or 'unnamed device'} ({self.address}){signal}"


def backend_available() -> bool:
    try:
        import bleak  # noqa: F401

        return True
    except Exception:
        return False


async def _scan(timeout: float) -> list[BleDevice]:
    from bleak import BleakScanner  # type: ignore

    discovered = await BleakScanner.discover(timeout=timeout)
    devices: list[BleDevice] = []
    for item in discovered:
        devices.append(
            BleDevice(
                address=getattr(item, "address", "unknown"),
                name=getattr(item, "name", "") or "",
                rssi=getattr(item, "rssi", None),
            )
        )
    return sorted(devices, key=lambda d: (-(d.rssi or -999), d.name.lower()))


def scan(timeout: float = 6.0) -> list[BleDevice]:
    if not backend_available():
        raise FeatureUnavailable(
            'Bluetooth scanning needs the bleak library. Install it with: pip install "jarvis-assistant[bluetooth]"'
        )
    if sys.platform.startswith("linux") and not _bluez_present():
        raise NotSupportedError(
            "The BlueZ service was not found. Install bluez and start the bluetooth service."
        )
    try:
        return asyncio.run(asyncio.wait_for(_scan(timeout), timeout=timeout + 10))
    except NotImplementedError as exc:  # pragma: no cover - platform dependent
        raise NotSupportedError("This platform does not provide a Bluetooth backend.") from exc
    except Exception as exc:  # pragma: no cover - hardware dependent
        raise FeatureUnavailable(f"The Bluetooth scan failed: {exc}") from exc


def _bluez_present() -> bool:
    import shutil

    return bool(shutil.which("bluetoothctl") or shutil.which("hciconfig"))


def describe(devices: list[BleDevice]) -> str:
    if not devices:
        return "I did not find any nearby Bluetooth LE devices."
    lines = [f"I found {len(devices)} nearby Bluetooth LE device(s) (scan only, no pairing):"]
    lines.extend(device.describe() for device in devices[:20])
    if len(devices) > 20:
        lines.append(f"…and {len(devices) - 20} more.")
    return "\n".join(lines)

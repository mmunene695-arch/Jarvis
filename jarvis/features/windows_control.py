"""Windows-only settings pages and volume control."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys

from ..errors import NotSupportedError, ValidationError

_WINDOWS = sys.platform.startswith("win")

#: Friendly name -> uri scheme understood by Windows 10/11.
SETTINGS_PAGES: dict[str, str] = {
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "audio": "ms-settings:sound",
    "volume": "ms-settings:sound",
    "bluetooth": "ms-settings:bluetooth",
    "devices": "ms-settings:bluetooth",
    "wifi": "ms-settings:network-wifi",
    "network": "ms-settings:network",
    "internet": "ms-settings:network",
    "battery": "ms-settings:batterysaver",
    "power": "ms-settings:powersleep",
    "storage": "ms-settings:storagesense",
    "apps": "ms-settings:appsfeatures",
    "privacy": "ms-settings:privacy",
    "camera": "ms-settings:privacy-webcam",
    "microphone": "ms-settings:privacy-microphone",
    "updates": "ms-settings:windowsupdate",
    "windows update": "ms-settings:windowsupdate",
    "about": "ms-settings:about",
    "notifications": "ms-settings:notifications",
    "datetime": "ms-settings:dateandtime",
    "time": "ms-settings:dateandtime",
    "startup": "ms-settings:startupapps",
    "default apps": "ms-settings:defaultapps",
}


def is_windows() -> bool:
    return _WINDOWS


def resolve_page(name: str) -> str:
    cleaned = (name or "").strip().lower()
    if cleaned in SETTINGS_PAGES:
        return SETTINGS_PAGES[cleaned]
    for key, uri in SETTINGS_PAGES.items():
        if key in cleaned:
            return uri
    raise ValidationError(
        "I do not know that settings page. Try display, sound, bluetooth, wifi, "
        "battery, privacy, camera, microphone or windows update."
    )


def open_settings(page: str) -> str:
    if not _WINDOWS:
        raise NotSupportedError("Windows Settings pages are only available on Windows.")
    uri = resolve_page(page)
    os.startfile(uri)  # type: ignore[attr-defined]
    return f"Opened the {page} settings page."


# ----------------------------------------------------------------------
# Volume control through the Core Audio COM endpoint
# ----------------------------------------------------------------------
def _volume_interface():  # pragma: no cover - requires Windows COM
    from ctypes import POINTER, Structure, c_uint, c_void_p, cast, windll
    from ctypes.wintypes import DWORD

    class GUID(Structure):
        _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

    class IAudioEndpointVolume(Structure):
        _fields_ = [("lpVtbl", POINTER(c_void_p))]

    CLSID_MMDeviceEnumerator = GUID(
        0xBCDE0395, 0xE52F, 0x467C,
        (ctypes.c_ubyte * 8)(0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E),
    )
    IID_IMMDeviceEnumerator = GUID(
        0xA95664D2, 0x9614, 0x4F35,
        (ctypes.c_ubyte * 8)(0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6),
    )
    IID_IAudioEndpointVolume = GUID(
        0x5CDF2C82, 0x841E, 0x4546,
        (ctypes.c_ubyte * 8)(0x97, 0x22, 0x0C, 0xF7, 0x40, 0x78, 0x22, 0x9A),
    )

    enum = c_void_p()
    windll.ole32.CoInitialize(None)
    hr = windll.ole32.CoCreateInstance(
        ctypes.byref(CLSID_MMDeviceEnumerator), None, 1,
        ctypes.byref(IID_IMMDeviceEnumerator), ctypes.byref(enum),
    )
    if hr != 0 or not enum:
        raise NotSupportedError("The Windows audio endpoint is not available")
    vtable = cast(enum, POINTER(POINTER(c_void_p))).contents
    # IMMDeviceEnumerator::GetDefaultAudioEndpoint is slot 4
    get_endpoint = ctypes.WINFUNCTYPE(ctypes.HRESULT, c_void_p, c_uint, c_uint, POINTER(c_void_p))(vtable[4])
    device = c_void_p()
    get_endpoint(enum, 0, 1, ctypes.byref(device))  # eRender, eMultimedia
    if not device:
        raise NotSupportedError("No default audio output device was found")
    device_vtbl = cast(device, POINTER(POINTER(c_void_p))).contents
    activate = ctypes.WINFUNCTYPE(ctypes.HRESULT, c_void_p, POINTER(GUID), DWORD, c_void_p, POINTER(c_void_p))(device_vtbl[3])
    iface = c_void_p()
    activate(device, ctypes.byref(IID_IAudioEndpointVolume), 1, None, ctypes.byref(iface))
    if not iface:
        raise NotSupportedError("The volume interface could not be opened")
    return cast(iface, POINTER(POINTER(c_void_p))).contents


def set_volume(level: int) -> str:  # pragma: no cover - requires Windows
    if not _WINDOWS:
        raise NotSupportedError("Volume control is only implemented for Windows.")
    if not 0 <= int(level) <= 100:
        raise ValidationError("Volume must be between 0 and 100")
    vtable = _volume_interface()
    scalar = ctypes.c_float(int(level) / 100.0)
    set_scalar = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.c_float, ctypes.c_void_p)(vtable[7])
    set_scalar(_volume_ptr(vtable), scalar, None)
    return f"System volume set to {int(level)} percent."


def set_mute(mute: bool) -> str:  # pragma: no cover - requires Windows
    if not _WINDOWS:
        raise NotSupportedError("Volume control is only implemented for Windows.")
    vtable = _volume_interface()
    setter = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)(vtable[14])
    setter(_volume_ptr(vtable), 1 if mute else 0, None)
    return "System audio muted." if mute else "System audio unmuted."


def _volume_ptr(vtable):  # pragma: no cover
    class _Holder(ctypes.Structure):
        _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]

    h = _Holder()
    h.lpVtbl = ctypes.cast(vtable, ctypes.POINTER(ctypes.c_void_p))
    return ctypes.cast(ctypes.pointer(h), ctypes.c_void_p)


def open_url_in_browser(url: str) -> str:  # pragma: no cover
    subprocess.Popen(["cmd", "/c", "start", "", url], close_fds=True)
    return f"Opened {url}"

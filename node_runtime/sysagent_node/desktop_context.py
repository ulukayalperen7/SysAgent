from __future__ import annotations

import base64
import io
import platform
import socket
from datetime import datetime, timezone
from typing import Any


def collect_desktop_context(include_screenshot: bool = True, max_width: int = 1280) -> dict[str, Any]:
    window = _active_window()
    screenshot = _screenshot(include_screenshot, max_width)
    payload: dict[str, Any] = {
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "activeWindowTitle": window.get("title"),
        "activeProcessName": window.get("process_name"),
        "screenWidth": screenshot.get("width"),
        "screenHeight": screenshot.get("height"),
        "screenshotMimeType": screenshot.get("mime_type"),
        "screenshotBase64": screenshot.get("base64"),
        "metadata": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "capture_backend": screenshot.get("backend"),
            "window_backend": window.get("backend"),
            "warnings": [*window.get("warnings", []), *screenshot.get("warnings", [])],
        },
    }
    return payload


def _active_window() -> dict[str, Any]:
    system = platform.system().lower()
    if system == "windows":
        return _windows_active_window()
    return {
        "title": None,
        "process_name": None,
        "backend": "unsupported",
        "warnings": ["Active window detection is not implemented for this OS yet."],
    }


def _windows_active_window() -> dict[str, Any]:
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        process_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        return {
            "title": buffer.value or None,
            "process_name": _process_name(process_id.value),
            "backend": "win32",
            "warnings": [],
        }
    except Exception as exc:
        return {
            "title": None,
            "process_name": None,
            "backend": "win32",
            "warnings": [f"Active window capture failed: {exc}"],
        }


def _process_name(process_id: int) -> str | None:
    try:
        import psutil

        return psutil.Process(process_id).name()
    except Exception:
        return None


def _screenshot(include_screenshot: bool, max_width: int) -> dict[str, Any]:
    if not include_screenshot:
        return {"backend": "disabled", "warnings": []}
    try:
        from PIL import ImageGrab

        image = ImageGrab.grab()
        width, height = image.size
        if max_width > 0 and width > max_width:
            new_height = max(1, int(height * (max_width / width)))
            image = image.resize((max_width, new_height))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=72, optimize=True)
        return {
            "width": image.width,
            "height": image.height,
            "mime_type": "image/jpeg",
            "base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
            "backend": "PIL.ImageGrab",
            "warnings": [],
        }
    except Exception as exc:
        return {
            "width": None,
            "height": None,
            "mime_type": None,
            "base64": None,
            "backend": "PIL.ImageGrab",
            "warnings": [f"Screenshot capture failed: {exc}"],
        }

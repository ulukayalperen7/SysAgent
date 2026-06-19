from __future__ import annotations

from typing import Any


def collect_metrics() -> dict[str, Any]:
    """Collect lightweight host metrics for heartbeat payloads.

    psutil is used when available because it is the reliable cross-platform
    path. The runtime still works without it; metrics simply remain unknown.
    """
    try:
        import psutil  # type: ignore
    except Exception:
        return {}

    payload: dict[str, Any] = {}
    try:
        payload["cpuUsage"] = _percent(psutil.cpu_percent(interval=0.1))
    except Exception:
        pass

    try:
        memory = psutil.virtual_memory()
        payload["ramUsage"] = _percent(memory.percent)
    except Exception:
        pass

    return {key: value for key, value in payload.items() if value is not None}


def _percent(value: object) -> int | None:
    try:
        rounded = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if rounded < 0 or rounded > 100:
        return None
    return rounded

"""Runtime dependency health checks for the AI Engine."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeDependency:
    name: str
    module: str
    required: bool
    purpose: str


RUNTIME_DEPENDENCIES: tuple[RuntimeDependency, ...] = (
    RuntimeDependency("fastapi", "fastapi", True, "AI Engine HTTP API"),
    RuntimeDependency("uvicorn", "uvicorn", True, "AI Engine ASGI server"),
    RuntimeDependency("pydantic_settings", "pydantic_settings", True, "environment configuration"),
    RuntimeDependency("langgraph", "langgraph", True, "agent workflow orchestration"),
    RuntimeDependency("crewai", "crewai", True, "diagnostics specialist agents"),
    RuntimeDependency("mcp", "mcp", True, "MCP transport and tool protocol"),
    RuntimeDependency("psutil", "psutil", True, "local read-only system inspection"),
    RuntimeDependency("psycopg", "psycopg", False, "PostgreSQL/Supabase Agent Hub access"),
    RuntimeDependency(
        "langgraph_checkpoint_postgres",
        "langgraph.checkpoint.postgres",
        False,
        "durable LangGraph PostgreSQL checkpointing",
    ),
)


def dependency_status() -> dict[str, dict[str, Any]]:
    """Return import availability without importing heavy runtime modules."""
    status: dict[str, dict[str, Any]] = {}
    for dependency in RUNTIME_DEPENDENCIES:
        available = _module_available(dependency.module)
        status[dependency.name] = {
            "module": dependency.module,
            "required": dependency.required,
            "available": available,
            "purpose": dependency.purpose,
        }
    return status


def runtime_health_status() -> dict[str, Any]:
    """Return a compact health payload suitable for a status endpoint."""
    dependencies = dependency_status()
    required_missing = [
        name
        for name, dependency in dependencies.items()
        if dependency["required"] and not dependency["available"]
    ]
    optional_missing = [
        name
        for name, dependency in dependencies.items()
        if not dependency["required"] and not dependency["available"]
    ]
    return {
        "status": "ready" if not required_missing else "degraded",
        "required_missing": required_missing,
        "optional_missing": optional_missing,
        "dependencies": dependencies,
    }


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

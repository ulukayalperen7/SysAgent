"""LangGraph checkpoint factory for SysAgent.

Memory checkpointing is the safe local default. PostgreSQL/Supabase
checkpointing can be enabled with:

LANGGRAPH_CHECKPOINT_BACKEND=postgres
LANGGRAPH_DATABASE_URL=postgresql://...
"""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from typing import Any

from core.config import settings

_postgres_context: AbstractContextManager[Any] | None = None
_last_active_backend = "memory"
_last_detail = "Memory checkpointing is active."


def build_checkpointer() -> Any:
    """Return a LangGraph checkpointer, falling back to memory when needed."""
    if settings.langgraph_checkpoint_backend.lower() == "postgres":
        checkpointer, detail = _build_postgres_checkpointer()
        if checkpointer is not None:
            _set_status("postgres", detail)
            return checkpointer
        _set_status("memory", detail)

    if settings.langgraph_checkpoint_backend.lower() != "postgres":
        _set_status("memory", "Memory checkpointing is active.")
    return _build_memory_checkpointer()


def checkpoint_status() -> dict[str, str]:
    """Return a lightweight status view for debugging runtime persistence."""
    configured = settings.langgraph_checkpoint_backend.lower()
    database_url = _checkpoint_database_url()
    active = _last_active_backend
    detail = _last_detail
    if configured == "postgres" and not database_url:
        active = "memory"
        detail = "PostgreSQL checkpointing requested but no database URL is configured."
    elif configured == "postgres" and database_url and active != "postgres":
        detail = "PostgreSQL checkpointing is configured; activation is confirmed when the graph is built."
    return {
        "configured_backend": configured,
        "active_backend": active,
        "database_url_configured": str(bool(database_url)),
        "detail": detail,
    }


def _build_memory_checkpointer() -> Any:
    try:
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver()
    except ImportError:
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()


def _build_postgres_checkpointer() -> tuple[Any | None, str]:
    database_url = _checkpoint_database_url()
    if not database_url:
        return None, "PostgreSQL checkpointing requested but no database URL is configured."

    os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError:
        return None, "langgraph-checkpoint-postgres is not installed."

    global _postgres_context
    try:
        _postgres_context = PostgresSaver.from_conn_string(database_url)
        checkpointer = _postgres_context.__enter__()
        if settings.langgraph_checkpoint_setup:
            checkpointer.setup()
        return checkpointer, "PostgreSQL checkpointing is active."
    except Exception as exc:
        _postgres_context = None
        return None, f"PostgreSQL checkpoint setup failed: {exc}"


def _checkpoint_database_url() -> str:
    raw_url = (settings.langgraph_database_url or settings.database_url or "").strip()
    if raw_url.startswith("jdbc:"):
        return ""
    return raw_url


def _set_status(active_backend: str, detail: str) -> None:
    global _last_active_backend, _last_detail
    _last_active_backend = active_backend
    _last_detail = detail

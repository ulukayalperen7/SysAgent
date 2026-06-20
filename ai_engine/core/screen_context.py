"""Screen context preparation for remote-device analysis.

This module keeps raw screenshot payloads out of LangGraph state after they are
optionally summarized into text.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from core.config import settings

ScreenSummarizer = Callable[[str, str], str | None]


def prepare_device_context_for_graph(
    device_context: dict[str, Any] | None,
    summarizer: ScreenSummarizer | None = None,
) -> dict[str, Any]:
    context = deepcopy(device_context or {"execution_mode": "local_backend"})
    screen = context.get("screen_context")
    if not isinstance(screen, dict):
        return context

    image_base64 = screen.pop("screen_image_base64", None)
    image_mime_type = screen.pop("screen_image_mime_type", None)
    if not image_base64 or not image_mime_type:
        return context

    screen["vision_status"] = "skipped"
    if not settings.screen_vision_enabled:
        screen["vision_reason"] = "screen vision is disabled"
        return context
    if len(str(image_base64)) > settings.screen_vision_max_base64_chars:
        screen["vision_reason"] = "screen image payload is too large"
        return context

    try:
        summary = (summarizer or summarize_screen_image)(str(image_mime_type), str(image_base64))
    except Exception as exc:
        screen["vision_status"] = "failed"
        screen["vision_reason"] = str(exc)[:240]
        return context

    if summary:
        screen["vision_status"] = "summarized"
        screen["vision_summary"] = summary[:1200]
    else:
        screen["vision_reason"] = "screen vision returned no summary"
    return context


def redact_device_context_for_audit(device_context: dict[str, Any] | None) -> dict[str, Any]:
    context = deepcopy(device_context or {"execution_mode": "local_backend"})
    screen = context.get("screen_context")
    if isinstance(screen, dict):
        screen.pop("screen_image_base64", None)
        screen.pop("screen_image_mime_type", None)
    return context


def summarize_screen_image(mime_type: str, image_base64: str) -> str | None:
    from langchain_core.messages import HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = settings.google_api_key or settings.gemini_api_key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY is not set.")

    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=api_key,
        temperature=0,
        request_timeout=settings.llm_request_timeout_seconds,
        retries=settings.llm_retries,
    )
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Summarize this desktop screenshot for an OS automation agent. "
                    "Focus on visible application, active window, obvious UI state, "
                    "selected/focused elements, and any warnings/dialogs. "
                    "Do not invent hidden information. Keep it under 5 short bullets."
                ),
            },
            {
                "type": "image_url",
                "image_url": f"data:{mime_type};base64,{image_base64}",
            },
        ]
    )
    response = llm.invoke([message])
    content = response.content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")).strip())
            else:
                parts.append(str(item).strip())
        return "\n".join(part for part in parts if part).strip() or None
    return str(content).strip() or None

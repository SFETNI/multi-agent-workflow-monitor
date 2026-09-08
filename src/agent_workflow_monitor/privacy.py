from __future__ import annotations

from pathlib import Path

from .models import SchemaError, public_text

PATH_MODES = frozenset({"hidden", "basename", "configured-label"})
FORBIDDEN_NORMALIZED_FIELDS = frozenset({"raw", "metadata", "source_payload", "original_event"})


def display_path(path: str | Path, mode: str = "hidden", configured_label: str | None = None) -> str:
    if mode not in PATH_MODES:
        raise SchemaError("unsupported path display mode")
    if mode == "hidden":
        return "Hidden"
    if mode == "basename":
        return str(path).replace(chr(92), "/").rsplit("/", 1)[-1] or "Hidden"
    if not configured_label or not configured_label.strip():
        return "Configured source"
    return public_text(configured_label, "source label", limit=80)


def reject_forbidden_fields(value: object) -> None:
    if isinstance(value, dict):
        if set(value) & FORBIDDEN_NORMALIZED_FIELDS:
            raise SchemaError("raw source fields are not allowed")
        for child in value.values():
            reject_forbidden_fields(child)
    elif isinstance(value, list):
        for child in value:
            reject_forbidden_fields(child)


def safe_error_message(_error: BaseException) -> str:
    return "Data unavailable. The configured source did not match the approved schema."

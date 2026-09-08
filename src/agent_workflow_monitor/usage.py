from __future__ import annotations

from .models import ContextUsage


def context_display(usage: ContextUsage) -> dict[str, str | float | None]:
    basis = usage.basis.replace("_", " ").title()
    if usage.percent is not None:
        return {"value": f"{usage.percent:.1f}%", "unit": "context", "percent": usage.percent, "basis": basis}
    if usage.used is not None:
        value = f"{usage.used / 1000:.1f}k" if usage.used >= 1000 else str(usage.used)
        return {"value": value, "unit": usage.unit, "percent": None, "basis": basis}
    return {"value": "Not measured", "unit": usage.unit, "percent": None, "basis": basis}

from __future__ import annotations

from datetime import datetime, timezone

from .models import Participant, SchemaError


def _age_seconds(timestamp: str | None, now: datetime) -> float | None:
    if timestamp is None:
        return None
    observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return (now - observed).total_seconds()


def derive_status(*, declared_status: str, status_basis: str, last_observed_at: str | None,
                  freshness_seconds: int, blocker_reported: bool = False,
                  human_action_reported: bool = False, responsibility: bool = False,
                  now: datetime | None = None) -> str:
    """Return a truthful display status; responsibility is intentionally non-evidentiary."""
    del responsibility
    if type(blocker_reported) is not bool or type(human_action_reported) is not bool:
        raise SchemaError("evidence flags must be boolean")
    if freshness_seconds < 1:
        raise SchemaError("freshness window must be positive")
    if blocker_reported:
        return "blocked"
    if human_action_reported:
        return "human_action"
    if declared_status in {"observed_active", "stale"}:
        if status_basis != "observed" or last_observed_at is None:
            return "idle_unknown"
        clock = now or datetime.now(timezone.utc)
        age = _age_seconds(last_observed_at, clock)
        if age is None or age < 0:
            return "idle_unknown"
        if age > freshness_seconds:
            return "stale"
        return "observed_active" if declared_status == "observed_active" else "idle_unknown"
    if declared_status in {"waiting", "idle_unknown"}:
        return declared_status
    if declared_status in {"blocked", "human_action"}:
        return "idle_unknown"
    raise SchemaError("unsupported declared status")


def should_animate(participant: Participant, *, freshness_seconds: int, now: datetime | None = None) -> bool:
    if participant.status != "observed_active" or participant.status_basis != "observed" or participant.last_observed_at is None:
        return False
    clock = now or datetime.now(timezone.utc)
    age = _age_seconds(participant.last_observed_at, clock)
    return age is not None and 0 <= age <= freshness_seconds

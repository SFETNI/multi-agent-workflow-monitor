from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .model_usage import TOKEN_FIELDS, validate_usage_event
from .models import SchemaError, exact_keys, optional_timestamp


def load_registry(path: str | Path) -> dict[str, Any]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SchemaError("pricing registry unavailable or malformed") from exc
    return validate_registry(raw)


def validate_registry(raw: Any) -> dict[str, Any]:
    row = exact_keys(raw, {"schema_version", "reviewed_at_utc", "providers", "entries"}, "pricing registry")
    if row["schema_version"] != 1 or not isinstance(row["providers"], list) or not isinstance(row["entries"], list):
        raise SchemaError("invalid pricing registry")
    optional_timestamp(row["reviewed_at_utc"], "registry review timestamp")
    if len(row["providers"]) != len(set(row["providers"])):
        raise SchemaError("duplicate pricing provider")
    seen: set[tuple[str, str, str]] = set()
    for item in row["entries"]:
        entry = exact_keys(item, {"provider", "canonical_model", "aliases", "effective_from_utc", "effective_to_utc", "currency", "unit", "rates", "rules", "provenance"}, "pricing entry")
        if entry["provider"] not in row["providers"] or entry["currency"] != "USD" or entry["unit"] != "per_1m_tokens":
            raise SchemaError("invalid pricing identity")
        if not isinstance(entry["aliases"], list) or any(not isinstance(alias, str) for alias in entry["aliases"]):
            raise SchemaError("invalid pricing aliases")
        start = optional_timestamp(entry["effective_from_utc"], "price start")
        end = optional_timestamp(entry["effective_to_utc"], "price end")
        if start is None or (end is not None and end <= start):
            raise SchemaError("invalid pricing interval")
        key = (entry["provider"], entry["canonical_model"], start)
        if key in seen:
            raise SchemaError("duplicate pricing revision")
        seen.add(key)
        if not isinstance(entry["rates"], dict) or not entry["rates"]:
            raise SchemaError("pricing entry has no rates")
        tool_dimensions = entry["rates"].get("tool_dimensions", [])
        if not isinstance(tool_dimensions, list):
            raise SchemaError("invalid tool pricing dimensions")
        numeric_rates = {key: value for key, value in entry["rates"].items() if key != "tool_dimensions"}
        if any(value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0) for value in numeric_rates.values()):
            raise SchemaError("invalid pricing rate")
        rules = exact_keys(entry["rules"], {"short_context", "long_context", "context_threshold_tokens", "peak_off_peak", "service_tier", "batch", "fast", "regional_multiplier", "conditions"}, "pricing rules")
        if not isinstance(rules["conditions"], list):
            raise SchemaError("invalid pricing conditions")
        exact_keys(entry["provenance"], {"source_type", "source_url", "retrieved_at_utc", "reviewed_at_utc", "review_status"}, "pricing provenance")
        if entry["provenance"]["source_type"] != "official_provider" or entry["provenance"]["review_status"] != "reviewed":
            raise SchemaError("unreviewed pricing entry")
    return row


def resolve_price(registry: dict[str, Any], provider: str | None, model: str | None, at_utc: str) -> dict[str, Any] | None:
    if not provider or not model:
        return None
    when = datetime.fromisoformat(at_utc.replace("Z", "+00:00"))
    matches = []
    for entry in registry["entries"]:
        if entry["provider"] != provider or model != entry["canonical_model"]:
            continue
        start = datetime.fromisoformat(entry["effective_from_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(entry["effective_to_utc"].replace("Z", "+00:00")) if entry["effective_to_utc"] else None
        if start <= when and (end is None or when < end):
            matches.append(entry)
    if len(matches) > 1:
        raise SchemaError("overlapping pricing revisions")
    return matches[0] if matches else None


def value_event(raw: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    event = validate_usage_event(raw)
    entry = resolve_price(registry, event["provider"], event["model"], event["event_at_utc"])
    if entry is None:
        return {"kind": "API_EQUIVALENT", "quality": "unknown", "low": None, "high": None, "currency": "USD"}
    rules = entry["rules"]
    context = event["pricing_context"]
    rates = entry["rates"]
    required_tier = rules.get("service_tier")
    if isinstance(required_tier, str) and context["service_tier"] != required_tier:
        return _unknown()
    if isinstance(required_tier, dict):
        rates = required_tier.get(context["service_tier"])
        if rates is None:
            return _unknown()
    for flag in ("batch", "fast"):
        variant = rules.get(flag)
        if context[flag]:
            if isinstance(variant, dict):
                rates = {**rates, **variant}
            elif variant is not True:
                return _unknown()
    peak = rules.get("peak_off_peak")
    if peak:
        if peak.get("timezone") != "UTC":
            return _unknown()
        hour = datetime.fromisoformat(event["event_at_utc"].replace("Z", "+00:00")).hour
        start, end = peak["peak_start_hour"], peak["peak_end_hour"]
        selected = peak["peak_rates"] if start <= hour < end else peak["off_peak_rates"]
        rates = {**rates, **selected}
    variants = [rates]
    threshold = rules.get("context_threshold_tokens")
    if threshold:
        tokens = context["context_tokens"]
        short, long = rules.get("short_context"), rules.get("long_context")
        if not short or not long:
            return _unknown()
        if tokens is None:
            variants = [{**rates, **short}, {**rates, **long}]
        else:
            variants = [{**rates, **(long if tokens >= threshold else short)}]
    amounts = [_calculate(event, variant) for variant in variants]
    if any(amount is None for amount in amounts):
        return _unknown()
    priced_amounts = [amount for amount in amounts if amount is not None]
    multiplier = rules.get("regional_multiplier")
    if multiplier:
        factor = multiplier.get("factor")
        regions = multiplier.get("regions")
        if not isinstance(factor, (int, float)) or factor < 1 or not isinstance(regions, list):
            return _unknown()
        if context["region"] is None:
            priced_amounts += [round(amount * factor, 8) for amount in priced_amounts]
        elif context["region"] in regions:
            priced_amounts = [round(amount * factor, 8) for amount in priced_amounts]
    low, high = min(priced_amounts), max(priced_amounts)
    return {"kind": "API_EQUIVALENT", "quality": "bounded" if low != high else "exact", "low": low, "high": high, "currency": "USD"}


def _unknown() -> dict[str, Any]:
    return {"kind": "API_EQUIVALENT", "quality": "unknown", "low": None, "high": None, "currency": "USD"}


def _calculate(event: dict[str, Any], rates: dict[str, Any]) -> float | None:
    dimensions = {
        "input_tokens": "input", "cached_input_tokens": "cached_input",
        "cache_write_tokens": "cache_write", "cache_write_5m_tokens": "cache_write_5m",
        "cache_write_1h_tokens": "cache_write_1h", "output_tokens": "output",
        "reasoning_tokens": "reasoning",
    }
    total = 0.0
    for token_key in TOKEN_FIELDS:
        if token_key == "reasoning_tokens":
            continue
        count = event[token_key]
        if count is not None and count > 0:
            rate = rates.get(dimensions[token_key])
            if rate is None:
                return None
            total += count / 1_000_000 * rate
    return round(total, 8)

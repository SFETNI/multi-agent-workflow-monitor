from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from agent_workflow_monitor.model_usage import UsageLedger, observed_tokens, validate_usage_event
from agent_workflow_monitor.models import SchemaError
from agent_workflow_monitor.pricing import load_registry, resolve_price, value_event
from agent_workflow_monitor.schema import load_snapshot

ROOT = Path(__file__).resolve().parents[1]


def event(**updates):
    row = deepcopy(load_snapshot(ROOT / "demo/public_snapshot.json").model_usage["events"][0])
    row.update(updates)
    return row


def test_exclusive_categories_do_not_double_count_reasoning():
    row = event(input_tokens=10, cached_input_tokens=20, output_tokens=30, reasoning_tokens=12, total_tokens=72)
    assert observed_tokens(row) == 60


def test_exact_model_date_resolves_without_fallback():
    registry = load_registry(ROOT / "config/pricing/model_pricing_registry.json")
    assert resolve_price(registry, "openai", "gpt-4.1", "2026-01-01T00:00:00Z")["canonical_model"] == "gpt-4.1"
    assert resolve_price(registry, "openai", "gpt-4.1-unknown", "2026-01-01T00:00:00Z") is None
    assert resolve_price(registry, "anthropic", "claude-sonnet-4-20250514", "2026-06-14T23:59:59Z") is not None
    assert resolve_price(registry, "anthropic", "claude-sonnet-4-20250514", "2026-06-15T00:00:00Z") is None
    assert resolve_price(registry, "anthropic", "claude-sonnet-5", "2026-06-29T23:59:59Z") is None
    assert resolve_price(registry, "anthropic", "claude-sonnet-5", "2026-06-30T00:00:00Z") is not None
    assert resolve_price(registry, "xai", "grok-4.6", "2026-09-18T23:59:59Z") is None
    assert resolve_price(registry, "xai", "grok-4.6", "2026-09-19T00:00:00Z") is not None
    assert resolve_price(registry, "google", "gemini-3.8-flash", "2026-09-01T23:59:59Z") is None
    assert resolve_price(registry, "google", "gemini-3.8-flash", "2027-01-01T00:00:00Z") is None


def test_effective_dated_promotion_applies_only_inside_window():
    registry = load_registry(ROOT / "config/pricing/model_pricing_registry.json")
    assert resolve_price(registry, "google", "gemini-3.8-flash", "2026-09-19T00:00:00Z") is not None
    assert resolve_price(registry, "google", "gemini-3.8-flash", "2027-01-01T00:00:00Z") is None


def test_cached_input_and_cache_write_dimensions_are_valued():
    registry = load_registry(ROOT / "config/pricing/model_pricing_registry.json")
    anthropic = deepcopy(load_snapshot(ROOT / "demo/public_snapshot.json").model_usage["events"][1])
    result = value_event(anthropic, registry)
    assert result["quality"] == "exact" and result["low"] > 0


def test_long_context_ambiguity_returns_bounds_not_guess():
    registry = load_registry(ROOT / "config/pricing/model_pricing_registry.json")
    grok = deepcopy(load_snapshot(ROOT / "demo/public_snapshot.json").model_usage["events"][2])
    result = value_event(grok, registry)
    assert result["quality"] == "bounded" and result["high"] > result["low"]


def test_peak_off_peak_is_selected_from_event_time():
    registry = deepcopy(load_registry(ROOT / "config/pricing/model_pricing_registry.json"))
    entry = next(item for item in registry["entries"] if item["canonical_model"] == "gpt-4.1")
    entry["rules"]["peak_off_peak"] = {
        "timezone": "UTC", "peak_start_hour": 12, "peak_end_hour": 18,
        "peak_rates": {"input": 4.0, "cached_input": 1.0, "output": 16.0},
        "off_peak_rates": {"input": 2.0, "cached_input": 0.5, "output": 8.0},
    }
    peak = value_event(event(event_at_utc="2026-09-19T12:08:00Z"), registry)
    off_peak = value_event(event(event_at_utc="2026-09-19T02:08:00Z"), registry)
    assert peak["quality"] == "exact" and peak["low"] == 2 * off_peak["low"]


def test_batch_fast_and_unknown_region_are_conservative():
    registry = deepcopy(load_registry(ROOT / "config/pricing/model_pricing_registry.json"))
    entry = next(item for item in registry["entries"] if item["canonical_model"] == "gpt-4.1")
    entry["rules"]["batch"] = {"input": 1.0, "cached_input": 0.25, "output": 4.0}
    entry["rules"]["regional_multiplier"] = {"regions": ["region-a"], "factor": 1.1}
    row = event()
    row["pricing_context"]["batch"] = True
    row["pricing_context"]["region"] = None
    result = value_event(row, registry)
    assert result["quality"] == "bounded" and result["high"] > result["low"]


def test_unpriced_and_unknown_model_stay_unknown():
    registry = load_registry(ROOT / "config/pricing/model_pricing_registry.json")
    unknown = deepcopy(load_snapshot(ROOT / "demo/public_snapshot.json").model_usage["events"][3])
    assert value_event(unknown, registry) == {"kind": "API_EQUIVALENT", "quality": "unknown", "low": None, "high": None, "currency": "USD"}


def test_supported_model_with_unpriced_nonzero_dimension_stays_unknown():
    registry = load_registry(ROOT / "config/pricing/model_pricing_registry.json")
    row = event(cache_write_tokens=1, total_tokens=None)
    assert value_event(row, registry) == {"kind": "API_EQUIVALENT", "quality": "unknown", "low": None, "high": None, "currency": "USD"}


def test_provider_value_is_not_billed_or_subscription_cost():
    row = event(billing_mode="PROVIDER_REPORTED_USAGE_VALUE", provider_reported_value=1.25, provider_reported_value_kind="quota")
    assert validate_usage_event(row)["billing_mode"] == "PROVIDER_REPORTED_USAGE_VALUE"
    assert row["billing_mode"] not in {"BILLED", "SUBSCRIPTION_FEE"}


def test_subscription_billing_remains_unknown_without_authoritative_evidence():
    row = event(billing_mode="UNKNOWN", provider_reported_value=None, provider_reported_value_kind=None)
    assert validate_usage_event(row)["billing_mode"] == "UNKNOWN"


def test_null_is_distinct_from_zero_and_private_fields_are_rejected():
    assert validate_usage_event(event(input_tokens=None))["input_tokens"] is None
    assert validate_usage_event(event(input_tokens=0))["input_tokens"] == 0
    contaminated = event(); contaminated["prompt"] = "private"
    with pytest.raises(SchemaError):
        validate_usage_event(contaminated)


def test_ledger_is_idempotent_and_pins_historical_valuation(tmp_path):
    row = event()
    encoded = json.dumps(validate_usage_event(row), sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
    ledger = UsageLedger(tmp_path / ".local/usage.sqlite3")
    assert ledger.ingest([row], {fingerprint: {"quality": "exact", "low": 1.0, "high": 1.0}}) == 1
    assert ledger.ingest([row], {fingerprint: {"quality": "exact", "low": 99.0, "high": 99.0}}) == 0
    assert ledger.rows()[0]["valuation"]["low"] == 1.0


def test_demo_reports_partial_pricing_coverage_honestly():
    usage = load_snapshot(ROOT / "demo/public_snapshot.json").model_usage
    assert usage["coverage"]["unknown_model_events"] == 1
    assert any(row["valuation_quality"] == "unknown" for row in usage["agents"])

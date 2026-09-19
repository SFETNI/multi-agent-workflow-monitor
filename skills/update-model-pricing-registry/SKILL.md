---
name: update-model-pricing-registry
description: Review public usage model IDs against official provider pricing and prepare a human-approved effective-dated registry update.
---

# Update model pricing registry

1. Inspect only normalized model/provider metadata.
2. Identify missing or stale exact entries.
3. Consult official provider sources and record exact URLs and retrieval dates.
4. Propose an effective-dated diff; never guess aliases or rates.
5. Require human approval before writing.
6. Validate the registry and tests after approval.

Do not expose credentials, fetch prices during normal monitor runtime, create fallback rates, or rewrite historical revisions. See [registry rules](references/registry-rules.md).

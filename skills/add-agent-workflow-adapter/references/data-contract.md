# Normalized targets

Use the repository's `config/public_snapshot.schema.json` and `docs/data-contract.md` as the authority. Prefer the existing `Participant`, `Workstream`, `ActivityEvent`, `HostMetrics`, and `PublicSnapshot` constructors because they enforce exact keys and cross-record invariants.

If the source cannot support a field truthfully, use the contract's null/not-measured representation. Do not invent placeholders that look measured.

# Data contract

`config/public_snapshot.schema.json` is the machine-readable public contract. Runtime validation in `models.py` also enforces cross-record references and measurement invariants.

## Participant

Each participant has a public ID, a configurable role key and label, workstream IDs, status and status basis, optional observation time, context usage, and storage usage. There is no field for a source identity, command, path, environment, raw record, or arbitrary metadata.

Context usage records `used`, `limit`, `unit`, `percent`, and `basis`. A percentage is valid only when `used` and a positive `limit` exist and the basis is `measured` or `configured`. `unverified` may show a count but no percentage. `not_measured` carries no numeric value.

Optional `illustrative: true` is allowed only in recorded_demo snapshots. It labels synthetic examples independently of the measured/configured denominator basis. Live snapshots reject illustrative values. The demo's illustrative percentages use an explicitly configured synthetic 200000-token denominator; no private limit is inferred.

Storage usage has `bytes`, signed integer or null `delta_bytes`, and `basis`. The v0.1 delta interval is three days. Negative deltas represent cleanup, for example -0.8 GiB / 3d; null means Not measured. Unmeasured storage carries neither size nor delta.

observed_active and stale require status_basis=observed plus an observation timestamp. Runtime freshness derives stale rather than trusting an arbitrary declaration. Future observations are unknown. Recorded blocked/human_action declarations are explicit source assertions, not inferences from responsibility.

## Workstream

A workstream has a public ID, label, status, public record label, and participant IDs. References must resolve within the same snapshot.

## Activity event

An event contains only its public ID/order/type, source and target public IDs, workstream ID, short action label, explicitly public message, display time, and provenance class. Adapters never forward a source object or free-form hidden payload.

## Host metrics

Host records contain load averages, free memory/disk, CPU count, uptime, optional aggregate GPU-memory values, measurement status, and observation time. Hostnames, addresses, process commands, environment values, and device serials are excluded.

Measured or stale host data requires an observation timestamp. Not measured host data carries no numeric values or timestamp. Host freshness is evaluated separately from participant activity.

Unknown normalized fields are rejected. Adding a field requires updating the schema, model, privacy tests, renderer tests, documentation, and release audit.

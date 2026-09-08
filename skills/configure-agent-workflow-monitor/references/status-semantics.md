# Status mapping

- Map fresh observed execution/activity to `observed_active` with `status_basis: observed` and an observation timestamp.
- Map explicit waiting to `waiting`.
- Let the freshness evaluator turn an old observation into `stale`.
- Map a blocker only from an explicit blocker field or record.
- Map human action only from an explicit decision/action request.
- Preserve ambiguity as `idle_unknown`.

Keep responsibility, NEXT ownership, and configured assignment separate from runtime evidence. Context denominator bases are `measured`, `configured`, `unverified`, and `not_measured`.

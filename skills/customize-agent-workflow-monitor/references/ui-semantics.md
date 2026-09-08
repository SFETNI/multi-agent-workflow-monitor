# UI semantics

- Solid state styling communicates status; animation communicates only fresh observed work.
- Waiting, stale, blocked, human-action, external, and unknown nodes remain static.
- Orchestrator supervision and active-worker motion must be visually distinct.
- Reduced-motion mode removes rotation/pulsing while retaining labels and state color.
- The map shows short deterministic action text; full public evidence belongs in Inspector/detail views.
- Unknown measurements render as `Not measured`, never as zero or an inferred percentage.

After a layout change, inspect native pixels rather than relying only on DOM presence. Confirm participant labels, activity text, context/storage cards, and host metrics are not clipped.

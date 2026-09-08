# Status semantics

| Status | Required basis |
|---|---|
| Observed active | Fresh observed runtime or activity timestamp |
| Waiting | Explicit waiting/assignment record without executing evidence |
| Stale | Observation older than the configured freshness window |
| Blocked | Explicit blocker record |
| Human action | Explicit human decision/action request |
| Idle/unknown | Insufficient evidence for another state |

Responsibility and next-action ownership never count as runtime evidence. A worker animates only while `observed_active` has an observed timestamp inside the freshness window. Stale, waiting, blocked, human-action, and unknown states do not animate.

The orchestrator visualization represents supervision only when it also has qualifying observed activity. Reduced-motion mode keeps the state signal but removes movement.

Measurement status is separate from participant status. Missing values remain `Not measured`; context percentages require a valid denominator and disclose whether that denominator was measured or configured.

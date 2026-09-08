---
name: configure-agent-workflow-monitor
description: Configure Agent Workflow Monitor when a user wants to connect an authorized complete public snapshot, set roles and freshness, or change private path display defaults.
---

# Configure Agent Workflow Monitor

Use demo mode first. Inspect only plausible read-only sources in the user-approved project scope and confirm the complete snapshot source before connecting it. v0.1 only supports source.adapter: snapshot. Fragment readers require a separate composition layer and are not standalone application inputs.

Create the live configuration under the gitignored `.local/` directory. Define public participant IDs, configurable roles, workstreams, freshness windows, approved metrics, and one of the path modes `hidden`, `basename`, or `configured-label`. Default to `hidden`.

Adapt the user's evidence to the accepted seven public display slots and two workstream slots; do not reproduce any private roster. Role labels and approved local icons are configurable. Arbitrary layout/cardinality is deferred. Relative source paths resolve beside the selected config. approved_metrics controls the serialized display, including hidden Inspector details. Use local_observation for live data and preserve the replay label for recorded_demo.

Do not scan an entire home directory, write to operational records, infer a missing state, turn responsibility into activity, convert missing measurements to zero, or compute a context percentage without a valid denominator. Start with fictional fixtures and run validation before opening a live source.

Read [configuration.md](references/configuration.md) for the decision checklist and [status-semantics.md](references/status-semantics.md) before mapping source statuses. Copy [example-config.yaml](assets/example-config.yaml) as the local starting point. Run `scripts/validate_config.py` from the repository root after each change.

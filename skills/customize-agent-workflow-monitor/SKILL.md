---
name: customize-agent-workflow-monitor
description: Customize roles, approved icons, labels, or freshness thresholds when adapting Agent Workflow Monitor to a user's workflow while retaining its accepted v2 presentation.
---

# Customize Agent Workflow Monitor

Prefer role registry and configuration changes over source edits. Keep role identity, runtime status, responsibility, and supervision separate. A role label or responsibility marker must never make a participant active or animated. v0.1 retains the accepted seven-slot, two-workstream layout; arbitrary topology/cardinality changes require a separate presentation pass. Static and runtime must continue to share one renderer.

Keep detailed evidence in Inspector/detail surfaces and the overview compact. Do not hard-code project, provider, account, host, or model labels into defaults. New icons must be local, accessible SVG assets with no scripts, remote references, metadata, or embedded raster payloads.

Preserve reduced-motion behavior, its explicit preview override, and read-only controls. Test native 1920×1080 and 1440×1000 layouts, a 1280×720 animation capture, narrow layout, reduced-motion/static mode, long configurable labels, missing data, and inactive/waiting states.

Read [ui-semantics.md](references/ui-semantics.md) before changing animation or density and [role-registry.md](references/role-registry.md) before adding a role. [role-example.svg](assets/role-example.svg) is a minimal local asset pattern.

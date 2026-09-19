---
name: add-workflow-trace-adapter
description: Map a workflow runtime into the provider-neutral manifest and normalized event stream without capturing content or adding controls.
---

# Add workflow trace adapter

1. Map static nodes and condition-labelled edges into workflow_manifest.json.
2. Map lifecycle metadata into normalized events.jsonl.
3. Keep organization, workflow, execution trace, and resources separate.
4. Exclude prompts, outputs, tools, checkpoint payloads, credentials, paths, and private IDs.
5. Validate with scripts/validate_workflow_trace.py.
6. Confirm the adapter is read-only and has no execution controls.

LangGraph is an example producer, not a requirement. See [adapter boundary](references/adapter-boundary.md).

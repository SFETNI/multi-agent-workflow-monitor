# Workflow adapters

An adapter emits two provider-neutral artifacts:

1. workflow_manifest.json
2. events.jsonl using the normalized event fields

Adapters should export lifecycle metadata, not prompts, completions, tool payloads, checkpoint contents, credentials, paths, or source-specific objects. Validate the result with scripts/validate_workflow_trace.py.

examples/langgraph demonstrates the boundary without making LangGraph a runtime dependency.

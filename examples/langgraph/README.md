# Optional LangGraph exporter example

LangGraph is not required by Agent Workflow Monitor. This directory demonstrates the boundary: a producer exports workflow_manifest.json and normalized events.jsonl, while the monitor reads only that provider-neutral data.

The included workflow_trace.json is deterministic synthetic output. No prompt, completion, checkpoint payload, private path, or control action is exported.

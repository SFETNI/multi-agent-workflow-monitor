# Architecture

The v0.1 app reads only a complete PublicSnapshot through SnapshotAdapter. Generic JSONL events and host/process metrics utilities return fragments; they are not wired as selectable application inputs. Source-specific optional adapters must produce a full snapshot or contribute to an explicitly implemented, tested composition layer.

Both static and local rendering call the same public projection in presentation.py. The canonical renderer lives under src/agent_workflow_monitor/renderer. build_demo.py materializes its assets and projected data. The local application embeds those same assets with safely escaped JSON in a minimal Streamlit wrapper. No simplified alternate overview remains.

The accepted seven-slot, two-workstream geometry is retained. Labels and icons are configurable, while arbitrary geometry/cardinality is deferred. Fixed standing relationships are presentation scaffolding, not evidence of execution. Recent Activity records all normalized events; only qualifying observed activity enables motion or an active edge capsule.

Approved metrics are excluded before serialization, not hidden with CSS. Source paths, raw payloads, provider formats, and filesystem errors never enter the projection. Runtime exceptions produce one generic UI error. The runner enforces loopback, CORS/XSRF, no error details/links, and no usage statistics.

The monitor never writes to source records or exposes orchestration/control actions. Source composition and private integrations remain outside the renderer and outside skill resources.

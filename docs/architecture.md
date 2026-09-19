# Architecture

Authorized local metadata flows through read-only adapters into a strict PublicSnapshot. The same deterministic projection drives Streamlit and the offline static replay.

The product keeps four layers separate:

- Organization: ownership and supervision.
- Workflow: possible transitions.
- Execution Trace: observed transitions in one run.
- Resources: context, model usage, API-equivalent value, storage, and host health.

Usage events may be retained in a local append-only SQLite ledger under .local/. The runtime database is gitignored and excluded from release archives. Pricing is resolved offline from the bundled effective-dated registry. Workflow rendering consumes generic JSON; LangGraph is only an optional producer example.

No monitor component controls an agent or workflow.

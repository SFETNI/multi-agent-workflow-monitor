# Public data contract

PublicSnapshot v2 extends the v1 snapshot with two optional objects:

- model_usage: normalized token metadata, registered-history aggregates, coverage, and valuation classifications.
- workflow_graph: one static manifest and a content-poor normalized execution event stream.

Both sections are optional. A v1 snapshot remains accepted. Null means unknown and is never treated as zero. Unknown fields are rejected by the Python validators.

No prompt, completion, tool payload, credential, account identity, private session ID, request payload, or private path belongs in the public contract.

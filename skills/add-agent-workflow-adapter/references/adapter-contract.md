# Adapter contract

An adapter receives an explicit source path/configuration and returns one documented normalized type. It must:

- read only and avoid locks that mutate metadata;
- fingerprint a file before and after parsing where practical;
- reject unknown input keys or deliberately discard them before normalization;
- validate primitive types before coercion;
- omit hostnames, commands, environments, session/account IDs, and source paths;
- attach an explicit observed/recorded/configured provenance class;
- raise a generic schema error whose message contains no source value.

Never store the original input in an exception, debug field, tooltip, DOM attribute, cache, or normalized object.

The v0.1 application consumes only a complete PublicSnapshot. JSONL events and process/host readers are tested fragment utilities. To release an integration, either normalize directly to PublicSnapshot or explicitly implement and test a composition layer that resolves participants, workstreams, events, measurements, and references. Do not add a fragment adapter to the selectable source enum without end-to-end composition tests.

Storage delta_bytes is signed over three days; do not discard cleanup deltas. Observed/stale records require timestamps. The smoke helper needs the product installed in the active dev environment and accepts a source, importable module, and adapter class; it checks read-only behavior, not UI completeness.

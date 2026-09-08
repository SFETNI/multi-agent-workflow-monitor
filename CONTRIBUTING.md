# Contributing

Keep the application read-only, local-first, and provider-neutral. Prefer configuration and adapters over presentation-specific parsing. New normalized fields require schema, model, privacy, malformed-input, and rendering tests. New adapters need fictional fixtures and evidence that source bytes and modification times do not change.

Do not commit runtime logs, process identifiers, state directories, secrets, private paths, raw payloads, or environment files. Do not add control-plane actions. Run the full tests and public-candidate audit before requesting review.
No CLA or special governance process is required for this project.

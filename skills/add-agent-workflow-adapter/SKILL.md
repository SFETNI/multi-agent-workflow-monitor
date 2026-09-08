---
name: add-agent-workflow-adapter
description: Add or review a read-only source adapter when connecting a new data format to Agent Workflow Monitor, preserving its complete-snapshot composition boundary.
---

# Add an Agent Workflow Adapter

Document the authorized source format and select only fields required by the normalized model. Implement the adapter behind `ReadOnlyAdapter`; open sources for reading, reject malformed or unknown raw fields, and return typed normalized objects without raw payloads, hidden metadata, source paths, or arbitrary dictionaries.

v0.1 selects only complete snapshot inputs. Event/host utilities are fragments, not independent app sources. A release-quality integration must produce a PublicSnapshot or contribute through a documented, tested composition layer that ultimately yields one. Returning a fragment does not wire it into the UI. Keep the accepted shared renderer intact.

Map status and timestamps with explicit provenance. Keep source-specific logic inside the adapter. Presentation and topology modules must not import it. If a user chooses a provider-specific local adapter, keep it optional and out of public defaults.

Add fictional valid, malformed, and leakage fixtures. Test that unknown fields are rejected, errors are public-safe, source bytes/hash/mtime remain unchanged, and no sentinel reaches normalized objects or rendered output. Run [adapter_smoke_test.py](scripts/adapter_smoke_test.py) against a disposable fictional source.

Read [adapter-contract.md](references/adapter-contract.md) before implementation and [data-contract.md](references/data-contract.md) when selecting fields.

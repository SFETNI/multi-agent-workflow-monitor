---
name: audit-agent-workflow-release
description: Audit an exact Agent Workflow Monitor candidate when preparing a release or rechecking changed content, including v2 renderer inheritance, privacy, isolation, and archive integrity.
---

# Audit an Agent Workflow Release

Audit only an exact candidate assembled from its explicit allowlist. Do not publish, push, tag, upload, create a repository, or select a license.

Run the candidate scanner with any project-private denylist supplied from outside the candidate. Run schema, status, privacy, adapter, rendering, sentinel, media, and archive tests. Inspect HTML, SVG, JSON, CSS, JavaScript, filenames, media metadata, archive member names, and unsupported files. Perform browser network/storage checks when the local browser driver is already available; do not install one automatically.

Run normal pytest in the development copy. Audit a fresh allowlisted stage, never exempt caches from the strict scanner. Copy the candidate to an unrelated temporary directory and run the demo/tests there, then stage again for the final strict audit. Inspect the 1920×1080 and 1440×1000 images and representative GIF frames. Confirm shared renderer inheritance and exact archive members/hashes.

Produce a receipt containing categories, counts, status, candidate/archive hashes, tool limitations, and unresolved publication decisions without reproducing sensitive strings. Read [release-audit.md](references/release-audit.md) for the gate and [privacy-boundary.md](references/privacy-boundary.md) for claim limits. Use [audit_release.py](scripts/audit_release.py) as the repository scanner entrypoint.

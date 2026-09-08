# Privacy Boundary

## Data flow

Only user-selected local sources enter a source adapter. The adapter extracts approved fields into the normalized model, discards unknown/raw content, and passes normalized records to the presentation layer. The application does not retain a hidden copy of source payloads.

Runtime state is local and belongs under `.local/` by default. The overview hides source paths. Optional path display modes are `hidden`, `basename`, and `configured-label`; absolute-path display is not supported.

## Bundled demo

The demo contains fictional public identifiers, generic workstreams, example operational text, and recorded example measurements. It contains no live connection or source mapping. Its HTML, scripts, styles, role graphics, screenshots, and GIF are local assets.

## Release audit

The release audit checks the explicit file allowlist, text and filename leakage patterns, symlinks, unsupported binaries/archives, runtime artifacts, media format/metadata, sentinel behavior, and archive members. An optional private denylist is supplied from outside the repository and is never copied into the candidate.

The audit does not establish absolute privacy for arbitrary future content, discover every possible secret, or certify third-party dependencies. Visual media still needs human inspection. Audit claims apply only to the exact candidate and archive hashes recorded in the audit packet.

Adding an adapter, changing content, rebuilding media, or changing archive members invalidates the prior receipt and requires a new audit.

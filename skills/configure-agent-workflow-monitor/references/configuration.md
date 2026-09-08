# Configuration checklist

1. Record the exact source files/directories the user authorized and why each is needed.
2. Select snapshot, the only complete v0.1 app source. Compose fragments outside the UI if required; do not select JSONL or metrics utilities as app inputs.
3. Assign fictional/public IDs and configurable role keys; do not reuse account, session, host, or provider identities.
4. Define workstreams and explicit freshness windows appropriate to their update cadence.
5. Approve only needed context, storage, and host measurements.
6. Choose `hidden` path display unless the user asks for a basename or configured label.
7. Put configuration and runtime output under `.local/` and confirm Git ignores it.
8. Validate, render fixtures, then compare source hashes and modification times before and after the first live read.

An absolute source path may exist in the user's local gitignored configuration. It must never enter normalized records, overview HTML, screenshots, archives, or committed examples.

Relative source paths resolve beside the chosen config. Only activity and host freshness windows are supported. Role entries contain label and icon; the latter must exist in the product renderer's roles directory. There is no configurable process freshness or unused state-root field. Signed delta_bytes covers three days. Missing values remain null, never zero.

# Release gate

A candidate passes only when:

- every shipped file is in the explicit allowlist and no symlink/runtime artifact exists;
- full tests and fictional sentinel controls pass;
- external denylist scanning, when supplied, finds no match;
- static browser requests remain same-origin with no storage/cookies/frames;
- media dimensions, frame count, duration, metadata, and visual content are accepted;
- an unrelated-directory copy runs without private-tree access;
- ZIP members exactly equal the allowlist and every member digest is recorded;
- deferred license, contact, ownership, and publication decisions are visible;
- exact candidate and archive hashes are recorded after all changes.

Any byte change invalidates the receipt. Report a failed category without echoing the triggering sensitive value.

Normal pytest creates development caches. Use the scanner's --staged option on that development tree or audit a fresh allowlisted copy. The scanner remains strict on the copy. The archive builder also audits its fresh stage before writing. Do not disable cache detection or copy private history. Verify unchanged accepted visual-source digests and both static and local rendering paths; a static-only pass is insufficient.

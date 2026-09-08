# Role registry

A role entry has a safe key, public label, and local SVG filename. The accepted public display slot controls layout identity; it does not imply activity. Users may add custom role entries and select their labels/icons for existing display slots. External Consultant / Collaborator is the public external default. Do not add ignored configuration fields.

Reject path separators in icon filenames. Keep role labels configurable and test them with long but bounded values. Do not use source-system identities as role keys.

Icons resolve inside the package renderer's roles directory. They must exist and pass the local SVG validator; remote references, scripts, and event handlers are rejected. Static and runtime projections use the same per-slot icon selection.

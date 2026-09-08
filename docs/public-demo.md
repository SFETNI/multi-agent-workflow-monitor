# Accepted v2 presentation

The visual authority is the exact public archive recorded in renderer-source.json. index.html, presentation.css, shell.css, geometry.js, and the base presentation.js are retained byte-for-byte in the package. app.js has narrow data-boundary additions for stale status, configured per-slot SVGs, and truthful local-observation labels; the drawing routines and accepted layout are retained.

Both the static replay and embedded runtime use this same renderer. A normalized synthetic fixture projects exactly to accepted_snapshot.json, including the seven views, two workstream rings, five session cards, complete handoffs, and approved illustrative values. The synthetic denominators are explicit fixture configuration; they are not recovered private telemetry.

The bundled 1920x1080 PNG, 1440x1000 PNG, and 1280x720 GIF are copied from that frozen accepted artifact. The GIF has 104 frames spanning 13 seconds and a complete lighthouse sweep. Private comparison/QA images are excluded.

Tests verify the unchanged visual-source hashes, exact approved data projection, shared runtime/static scripts and styles, and signed-delta/freshness behavior. Browser checks compare the two rendering paths at both widths, exercise all views and controls, and inspect motion and reduced-motion behavior. This establishes inheritance of the accepted public v2, not a new claim of pixel identity with every private application view.

The static page blocks network connections and uses local assets only. The embedded page inlines the same trusted code/styles and escapes public data to prevent script termination. Its CSP permits inline execution within the local iframe while still blocking connections, objects, fonts, and forms. No cookies or browser storage are written by the renderer.
